import brownie
from brownie import network, chain, interface
from decimal import Decimal
from ..utils import estimate_output_amount, approx, eth_to_cvxcrv
from ..utils.constants import (
    CLAIM_AMOUNT,
    TOKENS,
    ALCX,
    CVXCRV,
    VOTIUM_DISTRIBUTOR,
)


def test_third_party_claimed_single_workflow(
    fn_isolation,
    owner,
    bob,
    union_contract,
    set_mock_claims,
    claim_tree,
    merkle_distributor_v2,
    vault,
):
    network.gas_price("0 gwei")
    original_union_balance = interface.IERC20(CVXCRV).balanceOf(union_contract)
    proofs = claim_tree.get_proof(union_contract.address)
    params = [
        [token, proofs["claim"]["index"], CLAIM_AMOUNT, proofs["proofs"]]
        for token in TOKENS
        if token != ALCX
    ]
    single_claim_param = [
        [token, proofs["claim"]["index"], CLAIM_AMOUNT, proofs["proofs"]]
        for token in TOKENS
        if token == ALCX
    ]

    # Third party claims single token
    interface.IMultiMerkleStash(VOTIUM_DISTRIBUTOR).claimMulti(
        union_contract, single_claim_param, {"from": bob}
    )
    # Claim everything else
    union_contract.claim(params, {"from": owner})

    union_contract.setApprovals({"from": owner})
    expected_output_amount, eth_crv_ratio = estimate_output_amount(
        TOKENS, union_contract, 0
    )
    original_caller_balance = owner.balance()

    tx = union_contract.distribute(
        params + single_claim_param, 0, False, False, True, 0, {"from": owner}
    )

    distributor_balance = vault.balanceOfUnderlying(merkle_distributor_v2)
    union_balance = interface.IERC20(CVXCRV).balanceOf(union_contract)

    gas_used = tx.gas_price * tx.gas_used
    gas_fees = original_caller_balance - owner.balance() + gas_used
    gas_fees_in_crv = tx.events["Distributed"]["fees"]
    assert approx(eth_to_cvxcrv(gas_fees), gas_fees_in_crv, 0.5)
    assert approx(gas_used * eth_crv_ratio, gas_fees_in_crv, 0.5)
    assert distributor_balance > 0
    assert union_balance == original_union_balance
    assert gas_fees >= tx.gas_price
    assert merkle_distributor_v2.frozen() == True
    assert distributor_balance == expected_output_amount - gas_fees_in_crv


def test_third_party_claimed_all_workflow(
    fn_isolation,
    owner,
    bob,
    union_contract,
    set_mock_claims,
    claim_tree,
    merkle_distributor_v2,
    vault,
):
    network.gas_price("0 gwei")
    chain.snapshot()
    original_union_balance = interface.IERC20(CVXCRV).balanceOf(union_contract)
    proofs = claim_tree.get_proof(union_contract.address)
    params = [
        [token, proofs["claim"]["index"], CLAIM_AMOUNT, proofs["proofs"]]
        for token in TOKENS
    ]

    # Third party claims single token
    interface.IMultiMerkleStash(VOTIUM_DISTRIBUTOR).claimMulti(
        union_contract, params, {"from": bob}
    )

    union_contract.setApprovals({"from": owner})
    expected_output_amount, eth_crv_ratio = estimate_output_amount(
        TOKENS, union_contract, 0
    )
    original_caller_balance = owner.balance()

    tx = union_contract.distribute(params, 0, False, False, True, 0, {"from": owner})

    distributor_balance = vault.balanceOfUnderlying(merkle_distributor_v2)
    union_balance = interface.IERC20(CVXCRV).balanceOf(union_contract)

    gas_used = tx.gas_price * tx.gas_used
    gas_fees = original_caller_balance - owner.balance() + gas_used
    gas_fees_in_crv = tx.events["Distributed"]["fees"]
    assert approx(eth_to_cvxcrv(gas_fees), gas_fees_in_crv, 0.5)
    assert approx(gas_used * eth_crv_ratio, gas_fees_in_crv, 0.5)
    assert distributor_balance > 0
    assert union_balance == original_union_balance
    assert gas_fees >= tx.gas_price
    assert merkle_distributor_v2.frozen() == True
    assert distributor_balance == expected_output_amount - gas_fees_in_crv
