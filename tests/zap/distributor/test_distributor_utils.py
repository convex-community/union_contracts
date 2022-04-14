import brownie
from ...utils.constants import (
    CVXCRV,
    CURVE_CRV_ETH_POOL,
    CRV,
    CVXCRV_REWARDS,
    CURVE_CVXCRV_CRV_POOL,
    MAX_UINT256,
)
from brownie import interface, chain


def test_freeze_owner(owner, merkle_distributor):
    merkle_distributor.unfreeze({"from": owner})
    merkle_distributor.freeze({"from": owner})
    assert merkle_distributor.frozen() == True


def test_freeze_distributor(owner, union_contract, merkle_distributor):
    merkle_distributor.unfreeze({"from": owner})
    merkle_distributor.freeze({"from": union_contract})
    assert merkle_distributor.frozen() == True


def test_freeze_unauthorized(alice, merkle_distributor):
    with brownie.reverts("Admin or depositor only"):
        merkle_distributor.freeze({"from": alice})


def test_unfreeze(owner, merkle_distributor):
    merkle_distributor.freeze({"from": owner})
    merkle_distributor.unfreeze({"from": owner})
    assert merkle_distributor.frozen() == False


def test_unfreeze_unauthorized(alice, merkle_distributor):
    with brownie.reverts("Admin only"):
        merkle_distributor.unfreeze({"from": alice})


def test_update_root(owner, merkle_distributor):
    merkle_distributor.freeze({"from": owner})
    original_week = merkle_distributor.week()
    merkle_distributor.updateMerkleRoot("0x123", {"from": owner})
    assert merkle_distributor.week() == original_week + 1
    assert merkle_distributor.merkleRoot() == "0x123"


def test_update_root_unauthorized(alice, merkle_distributor):
    with brownie.reverts("Admin only"):
        merkle_distributor.updateMerkleRoot("0x123", {"from": alice})


def test_update_root_unfrozen(owner, merkle_distributor):
    merkle_distributor.unfreeze({"from": owner})
    with brownie.reverts("Contract not frozen."):
        merkle_distributor.updateMerkleRoot("0x123", {"from": owner})


def test_set_approvals(owner, merkle_distributor):
    merkle_distributor.setApprovals({"from": owner})
    crv = interface.IERC20(CRV)
    cvxcrv = interface.IERC20(CVXCRV)
    assert crv.allowance(merkle_distributor, CURVE_CRV_ETH_POOL) == MAX_UINT256
    assert cvxcrv.allowance(merkle_distributor, CVXCRV_REWARDS) == MAX_UINT256
    assert cvxcrv.allowance(merkle_distributor, CURVE_CVXCRV_CRV_POOL) == MAX_UINT256


def test_set_approvals_non_owner(alice, merkle_distributor):
    with brownie.reverts():
        merkle_distributor.setApprovals({"from": alice})


def test_update_admin(owner, alice, merkle_distributor):
    tx = merkle_distributor.updateAdmin(alice, {"from": owner})
    assert merkle_distributor.admin() == alice
    assert len(tx.events) == 1
    assert tx.events["AdminUpdated"]["oldAdmin"] == owner
    assert tx.events["AdminUpdated"]["newAdmin"] == alice
    chain.undo()


def test_update_admin_not_owner(owner, alice, merkle_distributor):
    with brownie.reverts("Admin only"):
        merkle_distributor.updateAdmin(alice, {"from": alice})
