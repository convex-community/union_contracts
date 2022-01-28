import brownie
from brownie import interface, chain, network
from decimal import Decimal
from ..utils import approx, estimate_output_amount
from ..utils.constants import CLAIM_AMOUNT, TOKENS, CVXCRV_REWARDS, CVXCRV


def test_claim_and_swap(
    owner, union_contract, set_mock_claims, vault, claim_tree, merkle_distributor_v2
):
    chain.snapshot()
    network.gas_price("0 gwei")
    original_union_balance = interface.IERC20(CVXCRV).balanceOf(union_contract)
    merkle_distributor_v2.unfreeze({"from": owner})
    proofs = claim_tree.get_proof(union_contract.address)
    params = [
        [token, proofs["claim"]["index"], CLAIM_AMOUNT, proofs["proofs"]]
        for token in TOKENS
    ]

    expected_output_amount, eth_crv_ratio = estimate_output_amount(
        TOKENS, union_contract, 0
    )
    union_dues = union_contract.unionDues()
    union_contract.setApprovals({"from": owner})
    with brownie.reverts():
        tx = union_contract.distribute(
            params, 0, True, False, True, expected_output_amount * 1.25, {"from": owner}
        )

    tx = union_contract.distribute(
        params, 0, True, False, True, expected_output_amount * 0.75, {"from": owner}
    )
    distributor_balance = vault.balanceOfUnderlying(merkle_distributor_v2)
    union_balance = (
        interface.IERC20(CVXCRV).balanceOf(union_contract) - original_union_balance
    )
    gas_fees = (
        int((union_balance + distributor_balance) * Decimal(10000 - union_dues))
        // 10000
        - distributor_balance
    )
    assert distributor_balance > 0
    assert union_balance > 0
    assert merkle_distributor_v2.frozen() == True
    assert approx(tx.gas_price * tx.gas_used * eth_crv_ratio, gas_fees, 0.5)
    assert union_balance + distributor_balance == expected_output_amount
    assert approx(
        union_balance / distributor_balance, union_dues / 10000, 0.3
    )  # moe due to gas refunds
    chain.revert()
