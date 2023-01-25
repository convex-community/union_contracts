import brownie
import pytest
from brownie import interface, chain
from decimal import Decimal

from ....utils.constants import ADDRESS_ZERO
from ....utils import approx, cvxcrv_balance, calc_staked_cvxcrv_harvest


@pytest.mark.parametrize("amount", [1e20])
def test_unique_withdrawal(
    fn_isolation, alice, owner, wrapper, vault, strategy, amount
):

    alice_initial_balance = cvxcrv_balance(alice)
    half_amount = int(Decimal(amount) / 2)
    vault.deposit(alice, amount, {"from": alice})
    tx = vault.withdraw(alice, half_amount, {"from": alice})
    penalty_amount = half_amount * vault.withdrawalPenalty() // 10000
    assert cvxcrv_balance(vault) == 0
    assert approx(
        cvxcrv_balance(alice),
        alice_initial_balance - half_amount - penalty_amount,
        1e-18,
    )
    assert approx(
        interface.ICvxCrvStaking(wrapper).balanceOf(strategy),
        half_amount + penalty_amount,
        1e-18,
    )
    assert approx(tx.events["Withdraw"]["_value"], half_amount - penalty_amount, 1e-18)
    assert tx.events["Withdraw"]["_from"] == alice
    assert tx.events["Withdraw"]["_to"] == alice
    assert approx(vault.balanceOf(alice), half_amount, 1e-18)


def test_withdraw_small(fn_isolation, alice, strategy, wrapper, owner, vault):
    alice_initial_balance = cvxcrv_balance(alice)
    vault.deposit(alice, 1, {"from": alice})
    vault.withdrawAll(alice, {"from": alice})
    assert cvxcrv_balance(alice) == alice_initial_balance  # no rewards
    assert interface.ICvxCrvStaking(wrapper).balanceOf(strategy) == 0
    assert vault.balanceOf(alice) == 0


def test_withdraw_all(fn_isolation, alice, owner, strategy, wrapper, vault):
    alice_initial_balance = cvxcrv_balance(alice)
    vault.depositAll(alice, {"from": alice})
    chain.sleep(100000)
    chain.mine(1)
    harvested = calc_staked_cvxcrv_harvest(strategy, wrapper)

    tx = vault.withdrawAll(alice, {"from": alice})
    assert approx(
        cvxcrv_balance(alice), alice_initial_balance + harvested, 1e-3
    )  # harvest as last to claim
    assert (
        cvxcrv_balance(alice) == alice_initial_balance + tx.events["Harvest"]["_value"]
    )
    assert (
        interface.ICvxCrvStaking(wrapper).balanceOf(strategy) == 0
    )  # last to claim == all withdrawn
    assert vault.balanceOf(alice) == 0
    chain.revert()


def test_withdraw_address_zero(fn_isolation, alice, owner, vault):
    vault.depositAll(alice, {"from": alice})
    with brownie.reverts("Invalid address!"):
        vault.withdrawAll(ADDRESS_ZERO, {"from": alice})
    with brownie.reverts("Invalid address!"):
        vault.withdraw(ADDRESS_ZERO, 10, {"from": alice})
