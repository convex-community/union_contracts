import brownie
from brownie.network.account import PublicKeyAccount
from tabulate import tabulate
from brownie import interface, chain, network
import pytest
from ..utils import (
    estimate_amounts_after_swap,
    approx,
    get_pirex_cvx_received,
)
from ..utils.adjust import simulate_adjust, get_spot_prices
from ..utils.constants import (
    CLAIM_AMOUNT,
    TOKENS,
    CVX,
    CRV,
    FXS,
    CVXCRV,
    MAX_WEIGHT_1E9,
    PRISMA,
    CRVUSD_TOKEN,
    SCRVUSD_VAULT,
)
from ..utils.crvusd import crvusd_to_scrvusd
from ..utils.cvxfxs import get_stk_cvxfxs_received
from ..utils.cvxprisma import get_stk_cvxprisma_received

data = [
    #    [MAX_WEIGHT_1E9, 0, 0],
    #    [0, MAX_WEIGHT_1E9, 0],
    #    [0, 0, MAX_WEIGHT_1E9],
    [0, 0, 0, 0, MAX_WEIGHT_1E9],
    [0, 333333334, 0, 0, 666666666],
    [0, 800000000, 100000000, 0, 100000000],
    [100000000, 0, 100000000, 0, 800000000],
    # [200000000, 200000000, 0, 600000000],
    # [100000000, 700000000, 100000000, 100000000],
    # [350000000, 250000000, 100000000, 300000000],
    # [300000000, 500000000, 50000000, 150000000],
]


@pytest.mark.parametrize("weights", data)
@pytest.mark.parametrize("lock", [True, False])
@pytest.mark.parametrize("option", [3])  # disable all but 3 b/c too much slippage
def test_swap_adjust_distribute(
    fn_isolation,
    owner,
    union_contract,
    set_mock_claims,
    vault,
    cvx_vault,
    fxs_vault,
    fxs_swapper,
    prisma_vault,
    prisma_swapper,
    claim_tree,
    crv_distributor,
    cvx_distributor,
    fxs_distributor,
    prisma_distributor,
    scrvusd_vault,
    scrvusd_distributor,
    weights,
    lock,
    option,
):
    token_symbols = ["CRV", "CVX", "FXS", "PRISMA", "CRVUSD"]
    print(f"Test with weights: {weights}")
    gas_refund = 3e16
    platform = PublicKeyAccount(union_contract.platform())
    scrvusd_receiver = scrvusd_distributor.platform()
    initial_platform_balance = platform.balance()
    fxs_swapper.updateOption(option, {"from": owner})
    platform_initial_crvusd_balance = interface.IERC20(SCRVUSD_VAULT).balanceOf(
        scrvusd_receiver
    )
    output_tokens = [union_contract.outputTokens(i) for i in range(len(weights))]
    vaults = [vault, cvx_vault, fxs_vault, prisma_vault, scrvusd_vault]
    distributors = [
        crv_distributor,
        cvx_distributor,
        fxs_distributor,
        prisma_distributor,
        scrvusd_distributor,
    ]

    proofs = claim_tree.get_proof(union_contract.address)
    params = [
        [token, proofs["claim"]["index"], CLAIM_AMOUNT, proofs["proofs"]]
        for token in TOKENS
    ]

    expected_eth_amount = estimate_amounts_after_swap(
        TOKENS, union_contract, 0, weights
    )
    original_caller_balance = owner.balance()

    # take chain snapshot here
    chain.snapshot()

    tx_swap = union_contract.swap(
        params, 0, True, 0, gas_refund, weights, {"from": owner}
    )

    gas_fees = owner.balance() - original_caller_balance
    assert gas_fees == gas_refund
    assert union_contract.balance() == expected_eth_amount - gas_fees

    fee_amount, output_amounts = simulate_adjust(
        union_contract, lock, weights, option, output_tokens, [0, 1, 2, 3, 4]
    )

    tx_adjust = union_contract.adjust(
        lock, weights, [0, 1, 2, 3, 4], [0, 0, 0, 0, 0], {"from": owner}
    )

    assert approx(platform.balance() - initial_platform_balance, fee_amount, 25e-3)

    spot_amounts = []
    for i, output_token in enumerate(output_tokens):
        # crv would have been swapped for CVXCRV already
        if output_token == CRV:
            output_token = CVXCRV
        balance = interface.IERC20(output_token).balanceOf(union_contract)
        # print(f"Balance {token_symbols[i]}: {balance}")
        # account for the fact that we leave 1 token unit for gas saving when swapping
        balance = 0 if balance == 1 else balance
        assert approx(balance, output_amounts[i], 25e-3)
        # calculate spoth ETH price and store
        price = get_spot_prices(output_token)
        # print(f"Price {output_token}: {price}")
        spot_amounts.append(balance * price)
        # unfreeze for distribution while we're at it
        distributors[i].unfreeze({"from": owner})

    # we now double check that the adjustment done on-chain with oracles
    # corresponds to the weights we get with spot prices
    total_eth_value = sum(spot_amounts)
    headers = ["Token", "Balance", "ETH Spot Value", "Weight", "Spot Weight"]
    reports = []
    actual_weights = []
    for i, output_token in enumerate(output_tokens):
        actual_weight = spot_amounts[i] / total_eth_value * MAX_WEIGHT_1E9
        actual_weights.append(actual_weight)
        reports.append(
            [
                output_token[:8] + "...",
                f"{output_amounts[i] * 1e-18:.2f}",
                f"{spot_amounts[i] * 1e-18:.2f}",
                f"{weights[i]}",
                f"{int(actual_weight)}",
            ]
        )

    print(tabulate(reports, headers=headers))
    for i, actual_weight in enumerate(actual_weights):
        # within 5%
        precision = 15e-1
        assert approx(weights[i], actual_weight, precision)

    # Account for discounts in curve pools
    fxs_index = output_tokens.index(FXS)
    output_amounts[fxs_index] = get_stk_cvxfxs_received(output_amounts[fxs_index])
    prisma_index = output_tokens.index(PRISMA)
    output_amounts[prisma_index] = get_stk_cvxprisma_received(
        output_amounts[prisma_index]
    )
    cvx_index = output_tokens.index(CVX)
    output_amounts[cvx_index] = get_pirex_cvx_received(output_amounts[cvx_index])

    tx_distribute = union_contract.distribute(weights)
    scrvusd_fee = scrvusd_distributor.platformFee()
    for i, output_token in enumerate(output_tokens):
        if weights[i] == 0:
            continue
        assert distributors[i].frozen() == True
        underlying = (
            vaults[i].balanceOfUnderlying(distributors[i])
            if vaults[i] not in [cvx_vault, scrvusd_vault]
            else vaults[i].convertToAssets(vaults[i].balanceOf(distributors[i]))
        )
        print(f"Expected {token_symbols[i]}: {output_amounts[i]}")
        if vaults[i] == scrvusd_vault:
            print(f"Net expected: {output_amounts[i] * (1 - scrvusd_fee/1e9)}")
        print(f"Realized {token_symbols[i]}: {underlying}")
        assert approx(underlying, output_amounts[i], 25e-3)

    # revert to test process incentives result
    chain.revert()

    tx = union_contract.processIncentives(
        params,
        0,
        True,
        lock,
        gas_refund,
        weights,
        [0, 1, 2, 3, 4],
        [0, 0, 0, 0, 0],
        {"from": owner},
    )

    for i, output_token in enumerate(output_tokens):
        if weights[i] == 0:
            continue
        assert distributors[i].frozen() == True
        underlying = (
            vaults[i].balanceOfUnderlying(distributors[i])
            if vaults[i] not in [cvx_vault, scrvusd_vault]
            else vaults[i].convertToAssets(vaults[i].balanceOf(distributors[i]))
        )

        if vaults[i] == scrvusd_vault:
            collected_fee = output_amounts[i] * scrvusd_fee / 1e9
            assert approx(underlying, output_amounts[i] - collected_fee, 25e-3)
            assert approx(
                collected_fee,
                interface.IERC20(SCRVUSD_VAULT).balanceOf(scrvusd_receiver)
                - platform_initial_crvusd_balance,
                25e-3,
            )
        else:
            assert approx(underlying, output_amounts[i], 25e-3)
