import brownie
from brownie import interface, chain, network
from decimal import Decimal
from ..utils import approx, estimate_output_amount, eth_to_cvxcrv
from ..utils.constants import CLAIM_AMOUNT, TOKENS, CVXCRV_REWARDS, CVXCRV


def test_claim_no_stake(
    fn_isolation,
    owner,
    union_contract,
    set_mock_claims,
    claim_tree,
    merkle_distributor_v2,
):
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

    union_contract.setApprovals({"from": owner})
    original_caller_balance = owner.balance()
    tx = union_contract.distribute(params, 0, True, False, False, 0, {"from": owner})
    distributor_balance = interface.IERC20(CVXCRV).balanceOf(merkle_distributor_v2)
    union_balance = (
        interface.IERC20(CVXCRV).balanceOf(union_contract) - original_union_balance
    )

    gas_used = tx.gas_price * tx.gas_used
    gas_fees = original_caller_balance - owner.balance() + gas_used
    gas_fees_in_crv = tx.events["Distributed"]["fees"]
    assert approx(eth_to_cvxcrv(gas_fees), gas_fees_in_crv, 0.5)
    assert approx(gas_used * eth_crv_ratio, gas_fees_in_crv, 0.5)
    assert distributor_balance > 0
    assert union_balance == 0
    assert merkle_distributor_v2.frozen() == True
    assert (
        union_balance + distributor_balance == expected_output_amount - gas_fees_in_crv
    )


def test_claim_no_stake_distributor_v1(
    fn_isolation, owner, union_contract, set_mock_claims, claim_tree, merkle_distributor
):
    network.gas_price("0 gwei")
    original_union_balance = interface.IERC20(CVXCRV).balanceOf(union_contract)
    union_contract.updateDistributor(merkle_distributor)
    merkle_distributor.unfreeze({"from": owner})
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
    tx = union_contract.distribute(params, 0, True, False, False, 0, {"from": owner})
    distributor_balance = interface.IERC20(CVXCRV).balanceOf(merkle_distributor)
    union_balance = (
        interface.IERC20(CVXCRV).balanceOf(union_contract) - original_union_balance
    )

    gas_used = tx.gas_price * tx.gas_used
    gas_fees = original_caller_balance - owner.balance() + gas_used
    gas_fees_in_crv = tx.events["Distributed"]["fees"]
    assert approx(eth_to_cvxcrv(gas_fees), gas_fees_in_crv, 0.5)
    assert approx(gas_used * eth_crv_ratio, gas_fees_in_crv, 0.5)
    assert distributor_balance > 0
    assert union_balance == 0
    assert merkle_distributor.frozen() == True
    assert (
        union_balance + distributor_balance == expected_output_amount - gas_fees_in_crv
    )
