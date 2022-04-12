import brownie
from tabulate import tabulate
from brownie import interface, chain, network
import pytest
from ..utils import (
    estimate_amounts_after_swap,
    approx,
)
from ..utils.adjust import simulate_adjust, get_spot_prices
from ..utils.constants import CLAIM_AMOUNT, TOKENS, CRV, FXS, CVXCRV
from ..utils.cvxfxs import estimate_lp_tokens_received

data = [
    [10000, 0, 0],
    [0, 10000, 0],
    [0, 0, 10000],
    [0, 8000, 2000],
    [2000, 0, 8000],
    [3334, 6666, 0],
    [1000, 8000, 1000],
    [3500, 2500, 4000],
    [3000, 5000, 2000],
]


@pytest.mark.parametrize("weights", data)
def test_swap_adjust_distribute(
    fn_isolation,
    owner,
    union_contract,
    set_mock_claims,
    vault,
    cvx_vault,
    fxs_vault,
    fxs_swapper,
    claim_tree,
    merkle_distributor_v2,
    cvx_distributor,
    fxs_distributor,
    weights,
):
    network.gas_price("0 gwei")
    lock = False
    option = fxs_swapper.swapOption()
    output_tokens = [union_contract.outputTokens(i) for i in range(len(weights))]
    vaults = [vault, cvx_vault, fxs_vault]
    distributors = [merkle_distributor_v2, cvx_distributor, fxs_distributor]

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

    tx_swap = union_contract.swap(params, 0, True, 0, weights, {"from": owner})
    gas_fees = owner.balance() - original_caller_balance

    assert union_contract.balance() == expected_eth_amount - gas_fees

    output_amounts = simulate_adjust(
        union_contract, lock, weights, option, output_tokens
    )

    tx_adjust = union_contract.adjust(lock, weights, [0, 0, 0], {"from": owner})
    spot_amounts = []
    for i, output_token in enumerate(output_tokens):
        # crv would have been swapped for CVXCRV already
        if output_token == CRV:
            output_token = CVXCRV
        balance = interface.IERC20(output_token).balanceOf(union_contract)
        assert balance == output_amounts[i]
        # calculate spoth ETH price and store
        price = get_spot_prices(output_token)
        spot_amounts.append(balance * price)
        # unfreeze for distribution while we're at it
        distributors[i].unfreeze({"from": owner})

    # we know double check that the adjustment done on-chain with oracles
    # corresponds to the weights we get with spot prices
    total_eth_value = sum(spot_amounts)
    headers = ["Token", "Balance", "ETH Spot Value", "Weight", "Spot Weight"]
    reports = []
    for i, output_token in enumerate(output_tokens):
        actual_weight = spot_amounts[i] / total_eth_value * 10000
        # within 3%
        assert approx(weights[i], actual_weight, 5e-2)
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

    # convert fxs to lp token to validate distributor balance
    fxs_index = output_tokens.index(FXS)
    output_amounts[fxs_index] = estimate_lp_tokens_received(output_amounts[fxs_index])

    tx_distribute = union_contract.distribute(weights)

    for i, output_token in enumerate(output_tokens):
        if weights[i] == 0:
            continue
        assert distributors[i].frozen() == True
        assert vaults[i].balanceOfUnderlying(distributors[i]) == output_amounts[i]

    # revert to test process incentives result
    chain.revert()

    tx = union_contract.processIncentives(
        params, 0, True, lock, [0, 0, 0], weights, {"from": owner}
    )

    for i, output_token in enumerate(output_tokens):
        if weights[i] == 0:
            continue
        assert distributors[i].frozen() == True
        # approximate as gas fees will be different
        assert approx(vaults[i].balanceOfUnderlying(distributors[i]), output_amounts[i])
