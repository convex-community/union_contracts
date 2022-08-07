import brownie
from brownie import chain

from ....utils.constants import AIRFORCE_SAFE, ADDRESS_ZERO


def test_harvest_non_vault(fn_isolation, alice, owner, vault, strategy):
    with brownie.reverts("Vault calls only"):
        strategy.harvest(AIRFORCE_SAFE, 0, False, {"from": owner})
    with brownie.reverts("Vault calls only"):
        strategy.harvest(AIRFORCE_SAFE, 0, False, {"from": alice})


def test_stake_non_vault(fn_isolation, alice, owner, vault, strategy):
    with brownie.reverts("Vault calls only"):
        strategy.stake(10, {"from": owner})
    with brownie.reverts("Vault calls only"):
        strategy.stake(10, {"from": alice})


def test_withdraw_non_vault(fn_isolation, alice, owner, vault, strategy):
    with brownie.reverts("Vault calls only"):
        strategy.withdraw(20, {"from": owner})
    with brownie.reverts("Vault calls only"):
        strategy.withdraw(20, {"from": alice})


def test_update_reward_token_non_owner(fn_isolation, alice, vault, strategy):
    with brownie.reverts("Ownable: caller is not the owner"):
        strategy.updateRewardToken(alice, alice, {"from": vault})
    with brownie.reverts("Ownable: caller is not the owner"):
        strategy.updateRewardToken(alice, alice, {"from": alice})


def test_add_reward_token_non_owner(fn_isolation, alice, vault, strategy):
    with brownie.reverts("Ownable: caller is not the owner"):
        strategy.addRewardToken(alice, alice, {"from": vault})
    with brownie.reverts("Ownable: caller is not the owner"):
        strategy.addRewardToken(alice, alice, {"from": alice})


def test_add_and_update_reward_token(fn_isolation, owner, strategy):
    strategy.addRewardToken(owner, owner, {"from": owner})
    total_tokens = strategy.totalRewardTokens()
    assert strategy.rewardTokens(total_tokens - 1) == owner
    assert strategy.rewardHandlers(owner) == owner
    strategy.updateRewardToken(owner, ADDRESS_ZERO)
    assert strategy.totalRewardTokens() == total_tokens
    assert strategy.rewardHandlers(owner) == ADDRESS_ZERO
