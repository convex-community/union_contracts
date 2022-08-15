import brownie
import pytest
from brownie import interface, chain
from decimal import Decimal

from ....utils.aurabal import calc_harvest_amount_aura
from ....utils.constants import AURA_BAL_STAKING, ADDRESS_ZERO
from ....utils import approx, aurabal_balance


@pytest.mark.parametrize("amount", [1e20])
def test_unique_partial_withdrawal(fn_isolation, alice, owner, vault, strategy, amount):
    alice_initial_balance = aurabal_balance(alice)
    half_amount = int(Decimal(amount) / 2)
    vault.deposit(alice, amount, {"from": alice})
    tx = vault.withdraw(alice, half_amount, {"from": alice})
    penalty_amount = half_amount * vault.withdrawalPenalty() // 10000
    assert aurabal_balance(vault) == 0
    assert approx(
        aurabal_balance(alice),
        alice_initial_balance - half_amount - penalty_amount,
        1e-18,
    )
    assert approx(
        interface.IBasicRewards(AURA_BAL_STAKING).balanceOf(strategy),
        half_amount + penalty_amount,
        1e-18,
    )
    assert approx(vault.balanceOf(alice), half_amount, 1e-18)


def test_withdraw_small(fn_isolation, alice, owner, strategy, vault):
    alice_initial_balance = aurabal_balance(alice)
    vault.deposit(alice, 1, {"from": alice})
    vault.withdrawAll(alice, {"from": alice})
    assert aurabal_balance(alice) == alice_initial_balance  # no rewards
    assert interface.IBasicRewards(AURA_BAL_STAKING).balanceOf(strategy) == 0
    assert vault.balanceOf(alice) == 0


def test_withdraw_address_zero(fn_isolation, alice, owner, vault):
    vault.depositAll(alice, {"from": alice})
    with brownie.reverts("Invalid address!"):
        vault.withdrawAll(ADDRESS_ZERO, {"from": alice})
    with brownie.reverts("Invalid address!"):
        vault.withdraw(ADDRESS_ZERO, 10, {"from": alice})


def test_withdraw_all(fn_isolation, alice, owner, vault, strategy):
    alice_initial_balance = aurabal_balance(alice)
    vault.depositAll(alice, {"from": alice})
    chain.sleep(100000)
    chain.mine(1)
    harvested = calc_harvest_amount_aura(strategy)

    tx = vault.withdrawAll(alice, {"from": alice})
    assert approx(
        aurabal_balance(alice), alice_initial_balance + harvested, 1e-3
    )  # harvest as last to claim
    assert (
        aurabal_balance(alice) == alice_initial_balance + tx.events["Harvest"]["_value"]
    )
    assert (
        interface.IBasicRewards(AURA_BAL_STAKING).balanceOf(strategy) == 0
    )  # last to claim == all withdrawn
    assert vault.balanceOf(alice) == 0
