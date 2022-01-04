import brownie
from ...utils.merkle import OrderedMerkleTree
from brownie import interface, chain
from ...utils.constants import CLAIM_AMOUNT


def test_claim(alice, bob, owner, merkle_distributor_v2, vault):
    chain.snapshot()
    claimers = [owner, alice, bob]
    data = [{"user": claimer.address, "amount": CLAIM_AMOUNT} for claimer in claimers]
    tree = OrderedMerkleTree(data)
    merkle_distributor_v2.freeze({"from": owner})
    merkle_distributor_v2.updateMerkleRoot(tree.get_root(), True, {"from": owner})
    merkle_distributor_v2.setApprovals({"from": owner})

    # test claim as cvxCrv
    proofs = tree.get_proof(alice.address)
    tx = merkle_distributor_v2.claim(
        proofs["claim"]["index"], alice.address, CLAIM_AMOUNT, proofs["proofs"]
    )
    assert vault.balanceOf(alice) == CLAIM_AMOUNT
    chain.revert()


def test_claim_no_double_dipping(alice, owner, merkle_distributor_v2):
    chain.snapshot()
    claimers = [alice]
    data = [{"user": claimer.address, "amount": CLAIM_AMOUNT} for claimer in claimers]
    tree = OrderedMerkleTree(data)
    merkle_distributor_v2.freeze({"from": owner})
    merkle_distributor_v2.updateMerkleRoot(tree.get_root(), True, {"from": owner})
    merkle_distributor_v2.setApprovals({"from": owner})

    proofs = tree.get_proof(alice.address)
    merkle_distributor_v2.claim(
        proofs["claim"]["index"], alice.address, CLAIM_AMOUNT, proofs["proofs"]
    )
    with brownie.reverts("Drop already claimed."):
        merkle_distributor_v2.claim(
            proofs["claim"]["index"], alice.address, CLAIM_AMOUNT, proofs["proofs"]
        )
    chain.revert()


def test_claim_wrong_proof(alice, bob, owner, merkle_distributor_v2):
    chain.snapshot()
    claimers = [alice]
    data = [{"user": claimer.address, "amount": CLAIM_AMOUNT} for claimer in claimers]
    tree = OrderedMerkleTree(data)
    merkle_distributor_v2.freeze({"from": owner})
    merkle_distributor_v2.updateMerkleRoot(tree.get_root(), True, {"from": owner})
    merkle_distributor_v2.setApprovals({"from": owner})

    proofs = tree.get_proof(alice.address)
    with brownie.reverts("Invalid proof."):
        merkle_distributor_v2.claim(
            proofs["claim"]["index"], bob.address, CLAIM_AMOUNT, proofs["proofs"]
        )
    chain.revert()
