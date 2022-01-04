import brownie
from brownie import network, chain, interface
from decimal import Decimal
from ..utils import estimate_output_amount, approx
from ..utils.constants import (
    CLAIM_AMOUNT,
    TOKENS,
    ALCX,
    CVXCRV,
    VOTIUM_DISTRIBUTOR,
)


def test_third_party_claimed_single_workflow(
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

    union_dues = union_contract.unionDues()
    union_contract.setApprovals({"from": owner})
    expected_output_amount, eth_crv_ratio = estimate_output_amount(
        TOKENS, union_contract, 0
    )

    tx = union_contract.distribute(
        params + single_claim_param, 0, False, False, {"from": owner}
    )

    distributor_balance = vault.claimable(merkle_distributor_v2)
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


def test_third_party_claimed_all_workflow(
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

    union_dues = union_contract.unionDues()
    union_contract.setApprovals({"from": owner})
    expected_output_amount, eth_crv_ratio = estimate_output_amount(
        TOKENS, union_contract, 0
    )

    tx = union_contract.distribute(params, 0, False, False, {"from": owner})

    distributor_balance = vault.claimable(merkle_distributor_v2)
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
