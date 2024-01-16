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
    CRV,
    FXS,
    CVXCRV,
    MAX_WEIGHT_1E9,
    UNBALANCED_TOKENS,
    PRISMA,
    CVX,
)
from ..utils.cvxfxs import get_stk_cvxfxs_received
from ..utils.cvxprisma import get_stk_cvxprisma_received


@pytest.mark.parametrize(
    "weights,adjust_order",
    [
        [[837299477, 27058091, 67821216, 67821216], [1, 2, 3, 0]],
        [[300000000, 600000000, 50000000, 50000000], [2, 3, 1, 0]],
        #        [[50000000, 50000000, 900000000], [0, 1, 2]],
        #        [[950000000, 0, 50000000], [2, 1, 0]],
    ],
)
@pytest.mark.parametrize("option", [3])
def test_swap_adjust_distribute(
    fn_isolation,
    owner,
    union_contract,
    set_mock_claims_unbalanced,
    vault,
    cvx_vault,
    fxs_vault,
    fxs_swapper,
    claim_tree,
    crv_distributor,
    cvx_distributor,
    fxs_distributor,
    prisma_vault,
    prisma_swapper,
    prisma_distributor,
    weights,
    adjust_order,
    option,
):
    gas_refund = 3e16
    lock = True
    platform = PublicKeyAccount(union_contract.platform())
    initial_platform_balance = platform.balance()
    fxs_swapper.updateOption(option, {"from": owner})
    output_tokens = [union_contract.outputTokens(i) for i in range(len(weights))]
    vaults = [vault, cvx_vault, fxs_vault, prisma_vault]
    distributors = [
        crv_distributor,
        cvx_distributor,
        fxs_distributor,
        prisma_distributor,
    ]

    proofs = claim_tree.get_proof(union_contract.address)
    params = [
        [token, proofs["claim"]["index"], CLAIM_AMOUNT, proofs["proofs"]]
        for token in UNBALANCED_TOKENS
    ]

    expected_eth_amount = estimate_amounts_after_swap(
        UNBALANCED_TOKENS, union_contract, 0, weights
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
        union_contract, lock, weights, option, output_tokens, adjust_order
    )

    with brownie.reverts():
        union_contract.adjust(
            lock, weights, adjust_order[::-1], [0, 0, 0, 0], {"from": owner}
        )

    tx_adjust = union_contract.adjust(
        lock, weights, adjust_order, [0, 0, 0, 0], {"from": owner}
    )

    assert approx(platform.balance() - initial_platform_balance, fee_amount, 5e-2)

    spot_amounts = []
    for i, output_token in enumerate(output_tokens):
        # crv would have been swapped for CVXCRV already
        if output_token == CRV:
            output_token = CVXCRV
        balance = interface.IERC20(output_token).balanceOf(union_contract)
        # account for the fact that we leave 1 token unit for gas saving when swapping
        balance = 0 if balance == 1 else balance
        assert approx(balance, output_amounts[i], 5e-2)
        # calculate spoth ETH price and store
        price = get_spot_prices(output_token)
        spot_amounts.append(balance * price)
        # unfreeze for distribution while we're at it
        distributors[i].unfreeze({"from": owner})
    print(f"Spots amounts: {spot_amounts}")
    # we know double check that the adjustment done on-chain with oracles
    # corresponds to the weights we get with spot prices
    total_eth_value = sum(spot_amounts)
    headers = ["Token", "Price", "Balance", "ETH Spot Value", "Weight", "Spot Weight"]
    reports = []
    for i, output_token in enumerate(output_tokens):
        actual_weight = spot_amounts[i] / total_eth_value * MAX_WEIGHT_1E9
        precision = 25e-2
        assert approx(weights[i], actual_weight, precision)
        reports.append(
            [
                output_token[:8] + "...",
                f"{spot_amounts[i] * 1e-18:.2f}",
                f"{output_amounts[i] * 1e-18:.2f}",
                f"{spot_amounts[i] * 1e-18:.2f}",
                f"{weights[i]}",
                f"{int(actual_weight)}",
            ]
        )

    print(tabulate(reports, headers=headers))

    # convert fxs to lp token to validate distributor balance
    fxs_index = output_tokens.index(FXS)
    output_amounts[fxs_index] = get_stk_cvxfxs_received(output_amounts[fxs_index])
    prisma_index = output_tokens.index(PRISMA)
    output_amounts[prisma_index] = get_stk_cvxprisma_received(
        output_amounts[prisma_index]
    )
    cvx_index = output_tokens.index(CVX)
    output_amounts[cvx_index] = get_pirex_cvx_received(output_amounts[cvx_index])

    tx_distribute = union_contract.distribute(weights)

    for i, output_token in enumerate(output_tokens):
        if weights[i] == 0:
            continue
        assert distributors[i].frozen() == True
        underlying = (
            vaults[i].balanceOfUnderlying(distributors[i])
            if vaults[i] != cvx_vault
            else vaults[i].convertToAssets(vaults[i].balanceOf(distributors[i]))
        )
        assert approx(underlying, output_amounts[i], 5e-2)

    # revert to test process incentives result
    chain.revert()

    tx = union_contract.processIncentives(
        params,
        0,
        True,
        lock,
        gas_refund,
        weights,
        adjust_order,
        [0, 0, 0, 0],
        {"from": owner},
    )

    for i, output_token in enumerate(output_tokens):
        if weights[i] == 0:
            continue
        assert distributors[i].frozen() == True
        underlying = (
            vaults[i].balanceOfUnderlying(distributors[i])
            if vaults[i] != cvx_vault
            else vaults[i].convertToAssets(vaults[i].balanceOf(distributors[i]))
        )
        assert approx(underlying, output_amounts[i], 5e-2)
