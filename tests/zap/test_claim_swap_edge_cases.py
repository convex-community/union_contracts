import brownie
from brownie import network, chain, interface
from ..utils import estimate_output_amount
from ..utils.constants import (
    CLAIM_AMOUNT,
    TOKENS,
    CVXCRV,
    CRV,
    CURVE_CVXCRV_CRV_POOL,
    CURVE_VOTING_ESCROW,
)


def test_claim_and_swap_no_discount(
    owner, union_contract, set_mock_claims, claim_tree, merkle_distributor_v2, vault
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
    crv = interface.IERC20(CRV)
    crv.approve(CURVE_CVXCRV_CRV_POOL, 2 ** 256 - 1, {"from": CURVE_VOTING_ESCROW})
    cvxcrv_swap = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL)
    cvxcrv_swap.add_liquidity(
        [crv.balanceOf(CURVE_VOTING_ESCROW), 0],
        0,
        CURVE_VOTING_ESCROW,
        {"from": CURVE_VOTING_ESCROW},
    )

    expected_output_amount, eth_crv_ratio = estimate_output_amount(
        TOKENS, union_contract, 0
    )
    union_contract.setApprovals({"from": owner})
    tx = union_contract.distribute(params, 0, True, True, {"from": owner})
    distributor_balance = vault.balanceOfUnderlying(merkle_distributor_v2)
    union_balance = (
        interface.IERC20(CVXCRV).balanceOf(union_contract) - original_union_balance
    )
    assert distributor_balance > 0
    assert union_balance > 0
    assert merkle_distributor_v2.frozen() == True
    assert union_balance + distributor_balance == expected_output_amount
    assert tx.events[-1]["locked"] == True
    chain.revert()


def test_claim_and_swap_not_owner(
    alice, owner, set_mock_claims, claim_tree, union_contract
):
    proofs = claim_tree.get_proof(union_contract.address)
    params = [
        [token, proofs["claim"]["index"], CLAIM_AMOUNT, proofs["proofs"]]
        for token in TOKENS
    ]
    union_contract.setApprovals({"from": owner})
    with brownie.reverts("Ownable: caller is not the owner"):
        union_contract.distribute(params, 0, True, False, {"from": alice})


def test_claim_and_swap_empty_claims(owner, union_contract):
    with brownie.reverts("No claims"):
        union_contract.distribute([], 0, True, False, {"from": owner})


def test_claim_not_owner(alice, union_contract):
    with brownie.reverts("Ownable: caller is not the owner"):
        union_contract.claim([[CVXCRV, 0, 0, ["0x0"]]], {"from": alice})
