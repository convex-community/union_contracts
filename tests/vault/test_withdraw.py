import brownie
import pytest
from brownie import interface, chain
from decimal import Decimal

from ..utils.constants import CVXCRV_REWARDS, ADDRESS_ZERO
from ..utils import approx, cvxcrv_balance, calc_harvest_amount_in_cvxcrv


@pytest.mark.parametrize("amount", [1e20])
def test_unique_withdrawal(alice, owner, vault, amount):
    chain.snapshot()
    alice_initial_balance = cvxcrv_balance(alice)
    half_amount = int(Decimal(amount) / 2)
    vault.setApprovals({"from": owner})
    vault.deposit(amount, {"from": alice})
    tx = vault.withdraw(alice, half_amount, {"from": alice})
    penalty_amount = half_amount * vault.withdrawalPenalty() // 10000
    assert cvxcrv_balance(vault) == 0
    assert approx(
        cvxcrv_balance(alice),
        alice_initial_balance - half_amount - penalty_amount,
        1e-18,
    )
    assert approx(
        interface.IBasicRewards(CVXCRV_REWARDS).balanceOf(vault),
        half_amount + penalty_amount,
        1e-18,
    )
    assert approx(tx.events["Unstake"]["amount"], half_amount - penalty_amount, 1e-18)
    assert tx.events["Unstake"]["user"] == alice
    assert approx(vault.balanceOf(alice), half_amount, 1e-18)
    chain.revert()


def test_withdraw_small(alice, owner, vault):
    chain.snapshot()
    alice_initial_balance = cvxcrv_balance(alice)
    vault.setApprovals({"from": owner})
    vault.deposit(1, {"from": alice})
    vault.withdrawAll(alice, {"from": alice})
    assert cvxcrv_balance(alice) == alice_initial_balance  # no rewards
    assert interface.IBasicRewards(CVXCRV_REWARDS).balanceOf(vault) == 0
    assert vault.balanceOf(alice) == 0
    chain.revert()


def test_withdraw_all(alice, owner, vault):
    chain.snapshot()
    alice_initial_balance = cvxcrv_balance(alice)
    vault.setApprovals({"from": owner})
    vault.depositAll({"from": alice})
    chain.sleep(100000)
    chain.mine(1)
    harvested = calc_harvest_amount_in_cvxcrv(vault)

    tx = vault.withdrawAll(alice, {"from": alice})
    assert approx(
        cvxcrv_balance(alice), alice_initial_balance + harvested, 1e-3
    )  # harvest as last to claim
    assert (
        cvxcrv_balance(alice) == alice_initial_balance + tx.events["Harvest"]["amount"]
    )
    assert (
        interface.IBasicRewards(CVXCRV_REWARDS).balanceOf(vault) == 0
    )  # last to claim == all withdrawn
    assert vault.balanceOf(alice) == 0
    chain.revert()


def test_withdraw_address_zero(alice, owner, vault):
    chain.snapshot()
    vault.setApprovals({"from": owner})
    vault.depositAll({"from": alice})
    with brownie.reverts("Receiver!"):
        vault.withdrawAll(ADDRESS_ZERO, {"from": alice})
    with brownie.reverts("Receiver!"):
        vault.withdraw(ADDRESS_ZERO, 10, {"from": alice})
    chain.revert()
