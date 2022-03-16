import brownie
from brownie import interface, chain, network
from decimal import Decimal
from ..utils import approx, estimate_output_amount, eth_to_cvxcrv
from ..utils.constants import CLAIM_AMOUNT, TOKENS, CVXCRV_REWARDS, CVXCRV


def test_claim_and_swap(
    fn_isolation,
    owner,
    union_contract,
    set_mock_claims,
    vault,
    claim_tree,
    merkle_distributor_v2,
):
    network.gas_price("20 gwei")
    merkle_distributor_v2.unfreeze({"from": owner})
    proofs = claim_tree.get_proof(union_contract.address)
    params = [
        [token, proofs["claim"]["index"], CLAIM_AMOUNT, proofs["proofs"]]
        for token in TOKENS
    ]

    expected_output_amount, eth_crv_ratio = estimate_output_amount(
        TOKENS, union_contract, 0
    )
    union_contract.setApprovals({"from": owner})
    original_caller_balance = owner.balance()
    tx = union_contract.distribute(params, 0, True, False, True, 0, {"from": owner})
    distributor_balance = vault.balanceOfUnderlying(merkle_distributor_v2)

    gas_used = tx.gas_price * tx.gas_used
    gas_fees = original_caller_balance - owner.balance() + gas_used
    gas_fees_in_crv = tx.events["Distributed"]["fees"]
    assert approx(eth_to_cvxcrv(gas_fees), gas_fees_in_crv, 0.5)
    assert approx(gas_used * eth_crv_ratio, gas_fees_in_crv, 0.5)
    assert distributor_balance > 0
    assert gas_fees >= tx.gas_price
    assert merkle_distributor_v2.frozen() == True
    assert distributor_balance == expected_output_amount - gas_fees_in_crv
