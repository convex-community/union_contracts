import brownie
from brownie import chain, interface

from ....utils.constants import AIRFORCE_SAFE, CVX, FXS


def test_vault_set_harvest_permissions_non_owner(fn_isolation, alice, vault):
    with brownie.reverts("Ownable: caller is not the owner"):
        vault.setHarvestPermissions(True, {"from": alice})


def test_vault_set_harvest_permissions(fn_isolation, owner, alice, bob, vault):
    vault.setHarvestPermissions(True, {"from": owner})
    assert vault.isHarvestPermissioned()
    # supply = 0 so we can call
    vault.harvest({"from": owner})
    # create supply
    vault.deposit(alice, 1e18, {"from": alice})
    with brownie.reverts("permissioned harvest"):
        vault.harvest({"from": owner})
    with brownie.reverts("permissioned harvest"):
        vault.harvest(10, {"from": owner})

    vault.updateAuthorizedHarvesters(bob, True, {"from": owner})
    chain.sleep(30)
    chain.mine(1)
    vault.harvest({"from": bob})
    vault.setHarvestPermissions(False, {"from": owner})
    assert not vault.isHarvestPermissioned()


def test_vault_update_authorized_harvesters(fn_isolation, owner, alice, bob, vault):
    vault.updateAuthorizedHarvesters(bob, True, {"from": owner})
    assert vault.authorizedHarvesters(bob)
    assert not vault.authorizedHarvesters(alice)
    vault.updateAuthorizedHarvesters(bob, False, {"from": owner})
    assert not vault.authorizedHarvesters(bob)


def test_vault_update_authorized_harvesters_non_owner(fn_isolation, alice, vault):
    with brownie.reverts("Ownable: caller is not the owner"):
        vault.updateAuthorizedHarvesters(AIRFORCE_SAFE, True, {"from": alice})


def test_vault_get_pending_rewards(fn_isolation, alice, vault):
    rewards = vault.claimableRewards({"from": alice})
    assert rewards[0][0] == FXS
    assert rewards[1][0] == CVX
