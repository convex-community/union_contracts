import brownie
from brownie import interface, chain, network
import pytest
from ..utils import (
    estimate_amounts_after_swap,
    approx,
)
from ..utils.constants import (
    CLAIM_AMOUNT,
    TOKENS,
    CURVE_CRV_ETH_POOL,
    CRV,
    CURVE_CVXCRV_CRV_POOL,
    CURVE_CVX_ETH_POOL,
    CVX,
)
from ..utils.cvxfxs import (
    estimate_lp_tokens_received,
    eth_fxs_curve,
    eth_fxs_uniswap,
    eth_fxs_unistable,
)


@pytest.mark.parametrize(
    "config",
    [
        {"index": 0, "weights": [10000, 0, 0]},
        {"index": 1, "weights": [0, 10000, 0]},
        {"index": 2, "weights": [0, 0, 10000]},
    ],
)
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
    config,
):
    network.gas_price("0 gwei")
    index = config["index"]
    weights = config["weights"]
    option = fxs_swapper.swapOption()
    vaults = [vault, cvx_vault, fxs_vault]
    distributors = [merkle_distributor_v2, cvx_distributor, fxs_distributor]
    current_vault = vaults[index]
    current_distributor = distributors[index]
    current_distributor.unfreeze({"from": owner})

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

    if index == 0:
        expected_crv_amount = interface.ICurveV2Pool(CURVE_CRV_ETH_POOL).get_dy(
            0, 1, ((expected_eth_amount - gas_fees))
        )
        expected_output_amount = interface.ICurveFactoryPool(
            CURVE_CVXCRV_CRV_POOL
        ).get_dy(
            0, 1, expected_crv_amount + interface.IERC20(CRV).balanceOf(union_contract)
        )
    elif index == 1:
        expected_output_amount = interface.ICurveV2Pool(CURVE_CVX_ETH_POOL).get_dy(
            0,
            1,
            (expected_eth_amount - gas_fees)
        ) + interface.IERC20(CVX).balanceOf(union_contract)
    else:

        if option == 0:
            fxs_amount = eth_fxs_curve(expected_eth_amount - gas_fees)
        elif option == 1:
            fxs_amount = eth_fxs_uniswap(expected_eth_amount - gas_fees)
        else:
            fxs_amount = eth_fxs_unistable(expected_eth_amount - gas_fees)

        expected_output_amount = estimate_lp_tokens_received(fxs_amount)

    tx_adjust = union_contract.adjust(False, weights, [0, 0, 0], {"from": owner})

    tx_distribute = union_contract.distribute(weights)

    distributor_balance = current_vault.balanceOfUnderlying(current_distributor)

    assert current_distributor.frozen() == True
    assert distributor_balance == expected_output_amount

    # revert to test process incentives result
    chain.revert()

    tx = union_contract.processIncentives(
        params, 0, True, False, [0, 0, 0], weights, {"from": owner}
    )

    assert current_distributor.frozen() == True
    # approximate as gas fees will be different
    assert approx(
        distributor_balance, current_vault.balanceOfUnderlying(current_distributor)
    )
