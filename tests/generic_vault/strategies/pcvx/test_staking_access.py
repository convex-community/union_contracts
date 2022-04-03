import brownie
from brownie import chain, interface

from ....utils.constants import FXS, CVXCRV_TOKEN, VE_FXS


def test_notify_reward_non_distributor(fn_isolation, alice, staking_rewards):
    with brownie.reverts("Distributor only"):
        staking_rewards.notifyRewardAmount(1000, {"from": alice})


def test_recover_erc_not_owner(fn_isolation, alice, staking_rewards):
    with brownie.reverts("Ownable: caller is not the owner"):
        staking_rewards.recoverERC20(CVXCRV_TOKEN, 20, {"from": alice})


def test_recover_erc_staking_token(fn_isolation, owner, pcvx, staking_rewards):
    with brownie.reverts("Cannot withdraw the staking token"):
        staking_rewards.recoverERC20(pcvx, 1e25, {"from": owner})


def test_recover_erc(fn_isolation, owner, staking_rewards):
    interface.IERC20(FXS).transfer(staking_rewards, 1e24, {"from": VE_FXS})
    staking_rewards.recoverERC20(FXS, 1e24, {"from": owner})
    assert interface.IERC20(FXS).balanceOf(owner) == 1e24


def test_set_rewards_duration_not_owner(fn_isolation, alice, staking_rewards):
    with brownie.reverts("Ownable: caller is not the owner"):
        staking_rewards.setRewardsDuration(20, {"from": alice})


def test_set_rewards_duration(fn_isolation, owner, staking_rewards):
    staking_rewards.setRewardsDuration(20, {"from": owner})
    assert staking_rewards.rewardsDuration() == 20


def test_set_distributor_not_owner(fn_isolation, alice, staking_rewards):
    with brownie.reverts("Ownable: caller is not the owner"):
        staking_rewards.setDistributor(CVXCRV_TOKEN, {"from": alice})


def test_set_distributor(fn_isolation, owner, staking_rewards):
    staking_rewards.setDistributor(CVXCRV_TOKEN, {"from": owner})
    assert staking_rewards.distributor() == CVXCRV_TOKEN
