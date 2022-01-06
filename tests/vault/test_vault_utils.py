import brownie
import pytest
from brownie import interface, chain

from ..utils.constants import (
    THREE_CRV_REWARDS,
    ADDRESS_ZERO,
    CVX_MINING_LIB,
    CVXCRV_REWARDS,
    CVXCRV_TOKEN,
)


def test_view_rewards(alice, vault):
    original_crv_rewards = vault.outstandingCrvRewards()
    original_cvx_rewards = vault.outstandingCvxRewards()
    original_3crv_rewards = vault.outstanding3CrvRewards()
    vault.deposit(alice, 1e20, {"from": alice})
    chain.mine(10)
    assert vault.outstandingCrvRewards() > original_crv_rewards
    assert vault.outstandingCvxRewards() > original_cvx_rewards
    assert vault.outstanding3CrvRewards() > original_3crv_rewards
    assert vault.outstandingCrvRewards() == interface.IBasicRewards(
        CVXCRV_REWARDS
    ).earned(vault)
    assert vault.outstandingCvxRewards() == interface.ICvxMining(
        CVX_MINING_LIB
    ).ConvertCrvToCvx(vault.outstandingCrvRewards())
    assert vault.outstanding3CrvRewards() == interface.IVirtualBalanceRewardPool(
        THREE_CRV_REWARDS
    ).earned(vault)
    chain.undo()


def test_total_holdings(alice, vault):
    vault.deposit(alice, 1e20, {"from": alice})
    assert vault.totalHoldings() == 1e20
    assert vault.totalHoldings() == interface.IBasicRewards(CVXCRV_REWARDS).balanceOf(
        vault
    )
    chain.undo()


def test_set_platform(alice, owner, vault):
    vault.setPlatform(alice, {"from": owner})
    assert vault.platform() == alice
    assert tx.events["PlatformUpdated"]["_platform"] == alice
    chain.undo()


def test_set_platform_address_zero(owner, vault):
    with brownie.reverts():
        vault.setPlatform(ADDRESS_ZERO, {"from": owner})


def test_set_platform_non_owner(alice, vault):
    with brownie.reverts("Ownable: caller is not the owner"):
        vault.setPlatform(alice, {"from": alice})


def test_set_platform_fee(owner, vault):
    vault.setPlatformFee(1234, {"from": owner})
    assert vault.platformFee() == 1234
    assert tx.events["PlatformFeeUpdated"]["_fee"] == 1234
    chain.undo()


def test_set_platform_fee_too_high(owner, vault):
    with brownie.reverts():
        vault.setPlatformFee(5000, {"from": owner})


def test_set_platform_fee_non_owner(alice, vault):
    with brownie.reverts("Ownable: caller is not the owner"):
        vault.setPlatformFee(1234, {"from": alice})


def test_set_call_incentive(owner, vault):
    vault.setCallIncentive(123, {"from": owner})
    assert vault.callIncentive() == 123
    assert tx.events["CallerIncentiveUpdated"]["_incentive"] == 123
    chain.undo()


def test_set_call_incentive_too_high(owner, vault):
    with brownie.reverts():
        vault.setCallIncentive(700, {"from": owner})


def test_set_call_incentive_non_owner(alice, vault):
    with brownie.reverts("Ownable: caller is not the owner"):
        vault.setCallIncentive(123, {"from": alice})


def test_set_withdraw_penalty(owner, vault):
    vault.setWithdrawalPenalty(123, {"from": owner})
    assert vault.withdrawalPenalty() == 123
    assert tx.events["WithdrawalPenaltyUpdated"]["_penalty"] == 123
    chain.undo()


def test_set_withdraw_penalty_too_high(owner, vault):
    with brownie.reverts():
        vault.setWithdrawalPenalty(700, {"from": owner})


def test_set_withdraw_penalty_non_owner(alice, vault):
    with brownie.reverts("Ownable: caller is not the owner"):
        vault.setWithdrawalPenalty(123, {"from": alice})


def test_balance_of_underlying(alice, bob, vault):
    vault.depositAll(alice, {"from": alice})
    vault.depositAll(bob, {"from": bob})
    assert (
        vault.balanceOfUnderlying(alice)
        == vault.balanceOf(alice) * vault.totalHoldings() / vault.totalSupply()
    )
    chain.undo(2)


def test_balance_of_underlying_no_users(alice, vault):
    with brownie.reverts("No users"):
        vault.balanceOfUnderlying(alice)


def test_underlying(vault):
    assert vault.underlying() == CVXCRV_TOKEN


def test_exchange_rate(alice, bob, vault):
    chain.snapshot()
    assert vault.exchangeRate() == int(1e18)
    vault.depositAll(alice, {"from": alice})
    assert vault.exchangeRate() == vault.totalHoldings() / vault.totalSupply()
    vault.depositAll(bob, {"from": bob})
    assert vault.exchangeRate() == vault.totalHoldings() / vault.totalSupply()
    chain.revert()
