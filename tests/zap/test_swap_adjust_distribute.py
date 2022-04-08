import brownie
from brownie import interface, chain, network
from decimal import Decimal
from ..utils import (
    approx,
    estimate_output_amount,
    eth_to_cvxcrv,
    estimate_amounts_after_swap,
)
from ..utils.constants import (
    CLAIM_AMOUNT,
    TOKENS,
    CVXCRV_REWARDS,
    CVXCRV,
    CURVE_CRV_ETH_POOL,
    CRV,
    CURVE_CVXCRV_CRV_POOL,
)


def test_swap_adjust_distribute(
    fn_isolation,
    owner,
    union_contract,
    set_mock_claims,
    vault,
    claim_tree,
    merkle_distributor_v2,
):
    network.gas_price("0 gwei")
    weights = [10000, 0, 0]
    merkle_distributor_v2.unfreeze({"from": owner})
    proofs = claim_tree.get_proof(union_contract.address)
    params = [
        [token, proofs["claim"]["index"], CLAIM_AMOUNT, proofs["proofs"]]
        for token in TOKENS
    ]

    expected_eth_amount = estimate_amounts_after_swap(
        TOKENS, union_contract, 0, weights
    )
    union_contract.setApprovals({"from": owner})
    original_caller_balance = owner.balance()
    tx_swap = union_contract.swap(params, 0, True, 0, weights, {"from": owner})
    gas_fees = owner.balance() - original_caller_balance

    assert union_contract.balance() == expected_eth_amount - gas_fees

    expected_crv_amount = interface.ICurveV2Pool(CURVE_CRV_ETH_POOL).get_dy(
        0, 1, ((expected_eth_amount - gas_fees))
    )
    expected_cvxcrv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(
        0, 1, expected_crv_amount + interface.IERC20(CRV).balanceOf(union_contract)
    )

    tx_adjust = union_contract.adjust(False, weights, [0, 0, 0], {"from": owner})

    tx_distribute = union_contract.distribute(weights)

    # tx = union_contract.processIncentives(params, 0, True, False, [0, 0, 0], weights, {"from": owner})
    distributor_balance = vault.balanceOfUnderlying(merkle_distributor_v2)

    assert merkle_distributor_v2.frozen() == True
    assert distributor_balance == expected_cvxcrv_amount
