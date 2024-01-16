import brownie
import pytest
from brownie import interface, chain
from decimal import Decimal

from ....utils.constants import ADDRESS_ZERO
from ....utils import approx, cvxprisma_balance
from ....utils.cvxprisma import (
    calc_staking_harvest_amount,
)


@pytest.mark.parametrize("amount", [1e20])
def test_unique_partial_withdrawal(
    fn_isolation, alice, owner, vault, strategy, amount, staking
):
    alice_initial_balance = cvxprisma_balance(alice)
    half_amount = int(Decimal(amount) / 2)
    vault.deposit(alice, amount, {"from": alice})
    tx = vault.withdraw(alice, half_amount, {"from": alice})
    penalty_amount = half_amount * vault.withdrawalPenalty() // 10000
    assert cvxprisma_balance(vault) == 0
    assert approx(
        cvxprisma_balance(alice),
        alice_initial_balance - half_amount - penalty_amount,
        1e-6,
    )
    assert approx(
        staking.balanceOf(strategy),
        half_amount + penalty_amount,
        1e-6,
    )
    assert approx(vault.balanceOf(alice), half_amount, 1e-6)


def test_withdraw_small(fn_isolation, alice, owner, strategy, vault, staking):
    alice_initial_balance = cvxprisma_balance(alice)
    vault.deposit(alice, 1, {"from": alice})
    vault.withdrawAll(alice, {"from": alice})
    assert cvxprisma_balance(alice) == alice_initial_balance  # no rewards
    assert staking.balanceOf(strategy) == 0
    assert vault.balanceOf(alice) == 0


def test_withdraw_address_zero(fn_isolation, alice, owner, vault):
    vault.depositAll(alice, {"from": alice})
    with brownie.reverts("Invalid address!"):
        vault.withdrawAll(ADDRESS_ZERO, {"from": alice})
    with brownie.reverts("Invalid address!"):
        vault.withdraw(ADDRESS_ZERO, 10, {"from": alice})


def test_withdraw_all(fn_isolation, alice, owner, vault, strategy, staking, harvester):
    alice_initial_balance = cvxprisma_balance(alice)
    vault.depositAll(alice, {"from": alice})
    chain.sleep(100000)
    chain.mine(1)
    harvested = calc_staking_harvest_amount(strategy, staking, 0)

    tx = vault.withdrawAll(alice, {"from": alice})
    assert approx(
        cvxprisma_balance(alice), alice_initial_balance + harvested, 1e-3
    )  # harvest as last to clai
    assert staking.balanceOf(strategy) == 0  # last to claim == all withdrawn
    assert vault.balanceOf(alice) == 0
