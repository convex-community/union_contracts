import brownie
from brownie import chain, interface

from ....utils.constants import (
    AIRFORCE_SAFE,
    FXS,
    VE_FXS, CVXFXS, ADDRESS_ZERO,
)


# STRATEGY ACCESS TESTS

def test_strategy_set_approvals(fn_isolation, alice, owner, vault, strategy, staking):
    interface.IERC20(CVXFXS).approve(staking, 0, {"from": strategy})
    strategy.setApprovals({"from": owner})
    assert interface.IERC20(CVXFXS).allowance(strategy, staking) == 2**256 - 1


def test_strategy_set_harvester_non_owner(fn_isolation, alice, owner, vault, strategy):
    with brownie.reverts("Ownable: caller is not the owner"):
        strategy.setHarvester(owner, {"from": alice})


def test_strategy_set_harvester_address_zero(fn_isolation, alice, owner, vault, strategy):
    with brownie.reverts():
        strategy.setHarvester(ADDRESS_ZERO, {"from": alice})


def test_strategy_set_harvester(fn_isolation, alice, owner, vault, strategy, staking):
    strategy.setHarvester(alice, {"from": owner})
    assert strategy.harvester() == alice
    assert staking.rewardRedirect(strategy) == alice


def test_strategy_total_underlying(fn_isolation, alice, owner, vault, strategy, staking):
    assert strategy.totalUnderlying() == staking.balanceOf(strategy)


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


def test_strategy_harvest_non_vault(fn_isolation, alice, owner, vault, strategy):
    with brownie.reverts("Vault calls only"):
        strategy.harvest(AIRFORCE_SAFE, 0, {"from": owner})
    with brownie.reverts("Vault calls only"):
        strategy.harvest(AIRFORCE_SAFE, 0, {"from": alice})


def test_strategy_rescue_token(fn_isolation, alice, owner, vault, strategy):
    original_owner_balance = interface.IERC20(FXS).balanceOf(owner)
    interface.IERC20(FXS).transfer(strategy, 1e24, {"from": VE_FXS})
    strategy.rescueToken(FXS, owner, 1e24, {"from": owner})
    assert interface.IERC20(FXS).balanceOf(owner) > original_owner_balance


def test_strategy_rescue_staking_token(
    fn_isolation, alice, owner, vault, strategy, staking
):
    with brownie.reverts("Cannot rescue staking token"):
        strategy.rescueToken(staking, owner, 0, {"from": owner})


def test_strategy_rescue_tokens_non_owner(fn_isolation, alice, harvester):
    with brownie.reverts("owner only"):
        harvester.rescueToken(FXS, alice, {"from": alice})

