import brownie
from brownie import chain, interface

from ....utils.constants import AIRFORCE_SAFE, FXS, CRV_TOKEN, CVX, THREECRV_TOKEN, VE_FXS


# STRATEGY ACCESS TESTS

def test_strategy_harvest_non_vault(fn_isolation, alice, owner, vault, strategy):
    with brownie.reverts("Vault calls only"):
        strategy.harvest(AIRFORCE_SAFE, 0, True, {"from": owner})
    with brownie.reverts("Vault calls only"):
        strategy.harvest(AIRFORCE_SAFE, 0, False, {"from": alice})


def test_strategy_stake_non_vault(fn_isolation, alice, owner, vault, strategy):
    with brownie.reverts("Vault calls only"):
        strategy.stake(10, {"from": owner})
    with brownie.reverts("Vault calls only"):
        strategy.stake(10, {"from": alice})


def test_strategy_withdraw_non_vault(fn_isolation, alice, owner, vault, strategy):
    with brownie.reverts("Vault calls only"):
        strategy.withdraw(20, {"from": owner})
    with brownie.reverts("Vault calls only"):
        strategy.withdraw(20, {"from": alice})


def test_strategy_set_harvester(fn_isolation, alice, owner, vault, strategy):
    with brownie.reverts("Ownable: caller is not the owner"):
        strategy.setHarvester(owner, {"from": alice})
    strategy.setHarvester(alice, {"from": owner})
    assert strategy.harvester() == alice


def test_strategy_set_reward_weights(fn_isolation, alice, vault, strategy):
    with brownie.reverts("Vault calls only"):
        strategy.setRewardWeight(2000, {"from": alice})


# HARVESTER ACCESS TESTS


def test_harvester_rescue_tokens_access(fn_isolation, alice, harvester):
    with brownie.reverts("owner only"):
        harvester.rescueToken(FXS, alice, {"from": alice})


def test_harvester_rescue_reward_tokens(fn_isolation, owner, harvester):
    with brownie.reverts("not allowed"):
        harvester.rescueToken(CRV_TOKEN, owner, {"from": owner})
    with brownie.reverts("not allowed"):
        harvester.rescueToken(CVX, owner, {"from": owner})
    with brownie.reverts("not allowed"):
        harvester.rescueToken(THREECRV_TOKEN, owner, {"from": owner})


def test_harvester_rescue_tokens(fn_isolation, owner, vault, harvester):
    original_owner_balance = interface.IERC20(FXS).balanceOf(owner)
    interface.IERC20(FXS).transfer(harvester, 1e24, {"from": VE_FXS})
    harvester.rescueToken(FXS, owner, {"from": owner})
    assert interface.IERC20(FXS).balanceOf(owner) > original_owner_balance


def test_harvester_set_slippage(fn_isolation, alice, owner, harvester):
    with brownie.reverts("owner only"):
        harvester.setSlippage(9500, {"from": alice})
    harvester.setSlippage(1000, {"from": owner})
    assert harvester.allowedSlippage() == 1000


def test_harvester_switch_oracle(fn_isolation, alice, owner, harvester):
    with brownie.reverts("owner only"):
        harvester.switchOracle({"from": alice})
    use_oracle = harvester.useOracle()
    harvester.switchOracle({"from": owner})
    assert use_oracle != harvester.useOracle()


def test_harvester_set_pending_owner(fn_isolation, alice, harvester):
    with brownie.reverts("owner only"):
        harvester.setPendingOwner(alice, {"from": alice})


def test_accept_pending_owner(fn_isolation, alice, bob, owner, harvester):
    with brownie.reverts("only new owner"):
        harvester.acceptOwnership({"from": owner})
    harvester.setPendingOwner(alice, {"from": owner})
    with brownie.reverts("only new owner"):
        harvester.acceptOwnership({"from": owner})
    with brownie.reverts("only new owner"):
        harvester.acceptOwnership({"from": bob})
    harvester.setPendingOwner(alice, {"from": owner})
    harvester.acceptOwnership({"from": alice})
    with brownie.reverts("owner only"):
        harvester.setPendingOwner(alice, {"from": owner})
    harvester.setPendingOwner(owner, {"from": alice})
    harvester.acceptOwnership({"from": owner})
    assert harvester.owner() == owner


def test_process_rewards(fn_isolation, alice, harvester):
    with brownie.reverts("strategy only"):
        harvester.processRewards(0, False, {"from": alice})


# VAULT ACCESS TESTS


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
    with brownie.reverts("slippage"):
        vault.harvest(1e22, {"from": bob})

    vault.setHarvestPermissions(False, {"from": owner})
    assert not vault.isHarvestPermissioned()


def test_vault_update_authorized_harvesters(fn_isolation, owner, alice, bob, vault):
    vault.updateAuthorizedHarvesters(bob, True, {"from": owner})
    assert vault.authorizedHarvesters(bob)
    assert not vault.authorizedHarvesters(alice)
    vault.updateAuthorizedHarvesters(bob, False, {"from": owner})
    assert not vault.authorizedHarvesters(bob)


def test_vault_update_authorized_harvesters(fn_isolation, alice, vault):
    with brownie.reverts("Ownable: caller is not the owner"):
        vault.updateAuthorizedHarvesters(AIRFORCE_SAFE, True, {"from": alice})


def test_vault_set_weight_unauthorized(fn_isolation, alice, vault):
    with brownie.reverts("authorized only"):
        vault.setRewardWeight(1000, {"from": alice})


def test_vault_set_weight_invalid(fn_isolation, owner, alice, vault):
    with brownie.reverts("invalid weight"):
        vault.setRewardWeight(100000, {"from": owner})


def test_vault_harvest_and_set_weight_unauthorized(fn_isolation, alice, vault):
    with brownie.reverts("authorized only"):
        vault.harvestAndSetRewardWeight(0, True, 1000, {"from": alice})
