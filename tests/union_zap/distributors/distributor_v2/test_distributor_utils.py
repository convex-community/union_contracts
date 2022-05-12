import brownie
from tests.utils.constants import (
    CVXCRV,
    CURVE_CRV_ETH_POOL,
    CRV,
    CVXCRV_REWARDS,
    CURVE_CVXCRV_CRV_POOL,
    ADDRESS_ZERO,
    MAX_UINT256,
)
from brownie import interface, chain


def test_freeze_owner(owner, merkle_distributor_v2):
    merkle_distributor_v2.unfreeze({"from": owner})
    merkle_distributor_v2.freeze({"from": owner})
    assert merkle_distributor_v2.frozen() == True


def test_freeze_distributor(owner, union_contract, merkle_distributor_v2):
    merkle_distributor_v2.unfreeze({"from": owner})
    merkle_distributor_v2.freeze({"from": union_contract})
    assert merkle_distributor_v2.frozen() == True


def test_freeze_unauthorized(alice, merkle_distributor_v2):
    with brownie.reverts("Admin or depositor only"):
        merkle_distributor_v2.freeze({"from": alice})


def test_unfreeze(owner, merkle_distributor_v2):
    merkle_distributor_v2.freeze({"from": owner})
    merkle_distributor_v2.unfreeze({"from": owner})
    assert merkle_distributor_v2.frozen() == False


def test_unfreeze_unauthorized(alice, merkle_distributor_v2):
    with brownie.reverts("Admin only"):
        merkle_distributor_v2.unfreeze({"from": alice})


def test_update_root(owner, merkle_distributor_v2):
    merkle_distributor_v2.freeze({"from": owner})
    original_week = merkle_distributor_v2.week()
    merkle_distributor_v2.updateMerkleRoot("0x123", False, {"from": owner})
    assert merkle_distributor_v2.week() == original_week + 1
    assert merkle_distributor_v2.merkleRoot() == "0x123"
    assert merkle_distributor_v2.frozen() == True


def test_update_root_and_unfreeze(owner, merkle_distributor_v2):
    merkle_distributor_v2.freeze({"from": owner})
    original_week = merkle_distributor_v2.week()
    merkle_distributor_v2.updateMerkleRoot("0x123", True, {"from": owner})
    assert merkle_distributor_v2.week() == original_week + 1
    assert merkle_distributor_v2.merkleRoot() == "0x123"
    assert merkle_distributor_v2.frozen() == False


def test_update_root_unauthorized(alice, merkle_distributor_v2):
    with brownie.reverts("Admin only"):
        merkle_distributor_v2.updateMerkleRoot("0x123", False, {"from": alice})


def test_update_root_unfrozen(owner, merkle_distributor_v2):
    merkle_distributor_v2.unfreeze({"from": owner})
    with brownie.reverts("Contract not frozen."):
        merkle_distributor_v2.updateMerkleRoot("0x123", False, {"from": owner})


def test_stake(owner, merkle_distributor_v2, vault):
    initial_claimable = vault.balanceOfUnderlying(merkle_distributor_v2)
    amount = 1e10
    interface.IERC20(CVXCRV).transfer(
        merkle_distributor_v2, amount, {"from": CVXCRV_REWARDS}
    )
    merkle_distributor_v2.stake({"from": owner})
    assert (
        vault.balanceOfUnderlying(merkle_distributor_v2) == initial_claimable + amount
    )


def test_stake_unauthorized(alice, merkle_distributor_v2):
    with brownie.reverts("Admin or depositor only"):
        merkle_distributor_v2.stake({"from": alice})


def test_set_approvals(owner, merkle_distributor_v2, vault):
    merkle_distributor_v2.setApprovals({"from": owner})
    crv = interface.IERC20(CRV)
    cvxcrv = interface.IERC20(CVXCRV)
    assert crv.allowance(merkle_distributor_v2, CURVE_CRV_ETH_POOL) == MAX_UINT256
    assert cvxcrv.allowance(merkle_distributor_v2, CVXCRV_REWARDS) == MAX_UINT256
    assert cvxcrv.allowance(merkle_distributor_v2, CURVE_CVXCRV_CRV_POOL) == MAX_UINT256
    assert cvxcrv.allowance(merkle_distributor_v2, vault) == MAX_UINT256


def test_set_approvals_non_owner(alice, merkle_distributor_v2):
    with brownie.reverts():
        merkle_distributor_v2.setApprovals({"from": alice})


def test_update_admin(owner, alice, merkle_distributor_v2):
    tx = merkle_distributor_v2.updateAdmin(alice, {"from": owner})
    assert merkle_distributor_v2.admin() == alice
    assert len(tx.events) == 1
    assert tx.events["AdminUpdated"]["oldAdmin"] == owner
    assert tx.events["AdminUpdated"]["newAdmin"] == alice
    chain.undo()


def test_update_admin_not_owner(owner, alice, merkle_distributor_v2):
    with brownie.reverts("Admin only"):
        merkle_distributor_v2.updateAdmin(alice, {"from": alice})


def test_update_depositor(owner, alice, merkle_distributor_v2):
    previous_depositor = merkle_distributor_v2.depositor()
    tx = merkle_distributor_v2.updateDepositor(alice, {"from": owner})
    assert merkle_distributor_v2.depositor() == alice
    assert len(tx.events) == 1
    assert tx.events["DepositorUpdated"]["oldDepositor"] == previous_depositor
    assert tx.events["DepositorUpdated"]["newDepositor"] == alice
    chain.undo()


def test_update_depositor_not_owner(owner, alice, merkle_distributor_v2):
    with brownie.reverts("Admin only"):
        merkle_distributor_v2.updateDepositor(alice, {"from": alice})


def test_update_depositor_address_zero(owner, merkle_distributor_v2):
    with brownie.reverts("Invalid address!"):
        merkle_distributor_v2.updateDepositor(ADDRESS_ZERO, {"from": owner})


def test_update_vault(owner, alice, merkle_distributor_v2):
    previous_vault = merkle_distributor_v2.vault()
    tx = merkle_distributor_v2.updateVault(alice, {"from": owner})
    assert merkle_distributor_v2.vault() == alice
    assert len(tx.events) == 1
    assert tx.events["VaultUpdated"]["oldVault"] == previous_vault
    assert tx.events["VaultUpdated"]["newVault"] == alice
    chain.undo()


def test_update_vault_not_owner(owner, alice, merkle_distributor_v2):
    with brownie.reverts("Admin only"):
        merkle_distributor_v2.updateVault(alice, {"from": alice})


def test_update_vault_address_zero(owner, merkle_distributor_v2):
    with brownie.reverts("Invalid address!"):
        merkle_distributor_v2.updateVault(ADDRESS_ZERO, {"from": owner})
