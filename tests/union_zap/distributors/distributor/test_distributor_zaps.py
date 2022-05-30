import brownie
from tests.utils.merkle import OrderedMerkleTree
from brownie import interface, chain
from tests.utils.constants import (
    CLAIM_AMOUNT,
    CVXCRV,
    CRV,
    CVX,
    CVXCRV_REWARDS,
    CURVE_CVX_ETH_POOL,
    CURVE_CVXCRV_CRV_POOL,
    CURVE_CRV_ETH_POOL,
)
from tests.utils import approx


def test_distrib_zaps(alice, bob, charlie, dave, erin, owner, merkle_distributor):
    chain.snapshot()
    cvxcrv = interface.IERC20(CVXCRV)
    crv = interface.IERC20(CRV)
    cvx = interface.IERC20(CVX)
    claimers = [alice, bob, charlie, dave, erin]
    data = [{"user": claimer.address, "amount": CLAIM_AMOUNT} for claimer in claimers]
    tree = OrderedMerkleTree(data)
    merkle_distributor.freeze({"from": owner})
    merkle_distributor.updateMerkleRoot(tree.get_root(), {"from": owner})
    merkle_distributor.unfreeze({"from": owner})
    merkle_distributor.setApprovals({"from": owner})

    # test claim as cvxCrv
    proofs = tree.get_proof(alice.address)
    alice_initial_balance = cvxcrv.balanceOf(alice)
    tx = merkle_distributor.claim(
        proofs["claim"]["index"], alice.address, CLAIM_AMOUNT, proofs["proofs"], 0
    )
    assert cvxcrv.balanceOf(alice) - alice_initial_balance == CLAIM_AMOUNT

    # test claim as Crv
    proofs = tree.get_proof(bob.address)
    crv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(
        1, 0, CLAIM_AMOUNT
    )
    bob_initial_balance = crv.balanceOf(bob)
    tx = merkle_distributor.claim(
        proofs["claim"]["index"], bob.address, CLAIM_AMOUNT, proofs["proofs"], 2
    )
    assert approx(crv.balanceOf(bob), bob_initial_balance + crv_amount, 0.01)

    # test claim as Cvx
    proofs = tree.get_proof(charlie.address)
    crv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(
        1, 0, CLAIM_AMOUNT
    )
    eth_amount = interface.ICurveV2Pool(CURVE_CRV_ETH_POOL).get_dy(1, 0, crv_amount)
    cvx_amount = interface.ICurveV2Pool(CURVE_CVX_ETH_POOL).get_dy(0, 1, eth_amount)
    tx = merkle_distributor.claim(
        proofs["claim"]["index"], charlie.address, CLAIM_AMOUNT, proofs["proofs"], 3
    )
    assert approx(cvx.balanceOf(charlie), cvx_amount, 0.01)

    # test claim as Eth
    proofs = tree.get_proof(dave.address)
    crv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(
        1, 0, CLAIM_AMOUNT
    )
    eth_amount = interface.ICurveV2Pool(CURVE_CRV_ETH_POOL).get_dy(1, 0, crv_amount)
    dave_original_balance = dave.balance()
    tx = merkle_distributor.claim(
        proofs["claim"]["index"], dave.address, CLAIM_AMOUNT, proofs["proofs"], 1
    )
    assert approx(dave.balance() - dave_original_balance, eth_amount, 0.01)

    # test claim and stake
    proofs = tree.get_proof(erin.address)
    erin_initial_balance = cvxcrv.balanceOf(erin)
    tx = merkle_distributor.claim(
        proofs["claim"]["index"], erin.address, CLAIM_AMOUNT, proofs["proofs"], 4
    )
    assert (
        interface.IBasicRewards(CVXCRV_REWARDS).balanceOf(erin.address) == CLAIM_AMOUNT
    )
    interface.IBasicRewards(CVXCRV_REWARDS).withdrawAll(False, {"from": erin})
    assert cvxcrv.balanceOf(erin) - erin_initial_balance == CLAIM_AMOUNT
    chain.revert()


def test_distrib_no_double_dipping(alice, owner, merkle_distributor):
    chain.snapshot()
    claimers = [alice]
    data = [{"user": claimer.address, "amount": CLAIM_AMOUNT} for claimer in claimers]
    tree = OrderedMerkleTree(data)
    merkle_distributor.freeze({"from": owner})
    merkle_distributor.updateMerkleRoot(tree.get_root(), {"from": owner})
    merkle_distributor.unfreeze({"from": owner})
    merkle_distributor.setApprovals({"from": owner})

    proofs = tree.get_proof(alice.address)
    merkle_distributor.claim(
        proofs["claim"]["index"], alice.address, CLAIM_AMOUNT, proofs["proofs"], 0
    )
    with brownie.reverts("Drop already claimed."):
        merkle_distributor.claim(
            proofs["claim"]["index"], alice.address, CLAIM_AMOUNT, proofs["proofs"], 0
        )
    chain.revert()


def test_distrib_wrong_proof(alice, bob, owner, merkle_distributor):
    claimers = [alice]
    data = [{"user": claimer.address, "amount": CLAIM_AMOUNT} for claimer in claimers]
    tree = OrderedMerkleTree(data)
    merkle_distributor.freeze({"from": owner})
    merkle_distributor.updateMerkleRoot(tree.get_root(), {"from": owner})
    merkle_distributor.unfreeze({"from": owner})
    merkle_distributor.setApprovals({"from": owner})

    proofs = tree.get_proof(alice.address)
    with brownie.reverts("Invalid proof."):
        merkle_distributor.claim(
            proofs["claim"]["index"], bob.address, CLAIM_AMOUNT, proofs["proofs"], 0
        )
