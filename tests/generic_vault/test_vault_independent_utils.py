import brownie
from brownie import interface, chain

from ..utils.constants import (
    ADDRESS_ZERO,
    CVXCRV_TOKEN,
)


def test_set_platform(alice, owner, dummy_vault):
    chain.snapshot()
    tx = dummy_vault.setPlatform(alice, {"from": owner})
    assert dummy_vault.platform() == alice
    assert tx.events["PlatformUpdated"]["_platform"] == alice
    chain.revert()


def test_set_platform_address_zero(owner, dummy_vault):
    with brownie.reverts():
        dummy_vault.setPlatform(ADDRESS_ZERO, {"from": owner})


def test_set_platform_non_owner(alice, dummy_vault):
    with brownie.reverts("Ownable: caller is not the owner"):
        dummy_vault.setPlatform(alice, {"from": alice})


def test_set_platform_fee(owner, dummy_vault):
    chain.snapshot()
    tx = dummy_vault.setPlatformFee(1234, {"from": owner})
    assert dummy_vault.platformFee() == 1234
    assert tx.events["PlatformFeeUpdated"]["_fee"] == 1234
    chain.revert()


def test_set_platform_fee_too_high(owner, dummy_vault):
    with brownie.reverts():
        dummy_vault.setPlatformFee(dummy_vault.MAX_PLATFORM_FEE() + 1, {"from": owner})


def test_set_platform_fee_non_owner(alice, dummy_vault):
    with brownie.reverts("Ownable: caller is not the owner"):
        dummy_vault.setPlatformFee(1234, {"from": alice})


def test_set_call_incentive(owner, dummy_vault):
    chain.snapshot()
    tx = dummy_vault.setCallIncentive(123, {"from": owner})
    assert dummy_vault.callIncentive() == 123
    assert tx.events["CallerIncentiveUpdated"]["_incentive"] == 123
    chain.revert()


def test_set_call_incentive_too_high(owner, dummy_vault):
    with brownie.reverts():
        dummy_vault.setCallIncentive(700, {"from": owner})


def test_set_call_incentive_non_owner(alice, dummy_vault):
    with brownie.reverts("Ownable: caller is not the owner"):
        dummy_vault.setCallIncentive(123, {"from": alice})


def test_set_withdraw_penalty(owner, dummy_vault):
    chain.snapshot()
    tx = dummy_vault.setWithdrawalPenalty(123, {"from": owner})
    assert dummy_vault.withdrawalPenalty() == 123
    assert tx.events["WithdrawalPenaltyUpdated"]["_penalty"] == 123
    chain.revert()


def test_set_withdraw_penalty_too_high(owner, dummy_vault):
    with brownie.reverts():
        dummy_vault.setWithdrawalPenalty(
            dummy_vault.MAX_WITHDRAWAL_PENALTY() + 1, {"from": owner}
        )


def test_set_withdraw_penalty_non_owner(alice, dummy_vault):
    with brownie.reverts("Ownable: caller is not the owner"):
        dummy_vault.setWithdrawalPenalty(123, {"from": alice})


def test_underlying(dummy_vault):
    assert dummy_vault.underlying() == CVXCRV_TOKEN


def test_set_strategy(owner, dummy_vault):
    chain.snapshot()
    tx = dummy_vault.setStrategy(CVXCRV_TOKEN, {"from": owner})
    assert dummy_vault.strategy() == CVXCRV_TOKEN
    assert tx.events["StrategySet"]["_strategy"] == CVXCRV_TOKEN
    with brownie.reverts():
        dummy_vault.setStrategy(CVXCRV_TOKEN, {"from": owner})
    chain.revert()


def test_set_strategy_address_zero(owner, dummy_vault):
    with brownie.reverts():
        dummy_vault.setStrategy(ADDRESS_ZERO, {"from": owner})


def test_set_strategy_non_owner(alice, dummy_vault):
    with brownie.reverts("Ownable: caller is not the owner"):
        dummy_vault.setWithdrawalPenalty(CVXCRV_TOKEN, {"from": alice})
