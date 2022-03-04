import brownie
import pytest
from brownie import interface, chain
from decimal import Decimal

from ....utils.constants import CVXFXS_STAKING_CONTRACT, ADDRESS_ZERO
from ....utils import approx, cvxfxs_lp_balance
from ....utils.cvxfxs import calc_harvest_amount_curve, estimate_lp_tokens_received


@pytest.mark.parametrize("amount", [1e20])
def test_unique_partial_withdrawal(alice, owner, vault, strategy, amount):
    chain.snapshot()
    strategy.setSwapOption(0, {"from": owner})
    alice_initial_balance = cvxfxs_lp_balance(alice)
    half_amount = int(Decimal(amount) / 2)
    vault.deposit(alice, amount, {"from": alice})
    tx = vault.withdraw(alice, half_amount, {"from": alice})
    penalty_amount = half_amount * vault.withdrawalPenalty() // 10000
    assert cvxfxs_lp_balance(vault) == 0
    assert approx(
        cvxfxs_lp_balance(alice),
        alice_initial_balance - half_amount - penalty_amount,
        1e-18,
    )
    assert approx(
        interface.IBasicRewards(CVXFXS_STAKING_CONTRACT).balanceOf(strategy),
        half_amount + penalty_amount,
        1e-18,
    )
    assert approx(tx.events["Withdraw"]["value"], half_amount - penalty_amount, 1e-18)
    assert approx(vault.balanceOf(alice), half_amount, 1e-18)
    chain.revert()


def test_withdraw_small(alice, owner, strategy, vault):
    chain.snapshot()
    strategy.setSwapOption(0, {"from": owner})
    alice_initial_balance = cvxfxs_lp_balance(alice)
    vault.deposit(alice, 1, {"from": alice})
    vault.withdrawAll(alice, {"from": alice})
    assert cvxfxs_lp_balance(alice) == alice_initial_balance  # no rewards
    assert interface.IBasicRewards(CVXFXS_STAKING_CONTRACT).balanceOf(strategy) == 0
    assert vault.balanceOf(alice) == 0
    chain.revert()


def test_withdraw_address_zero(alice, owner, vault):
    chain.snapshot()
    vault.depositAll(alice, {"from": alice})
    with brownie.reverts("Invalid address!"):
        vault.withdrawAll(ADDRESS_ZERO, {"from": alice})
    with brownie.reverts("Invalid address!"):
        vault.withdraw(ADDRESS_ZERO, 10, {"from": alice})
    chain.revert()


def test_withdraw_all(alice, owner, vault, strategy):
    chain.snapshot()
    strategy.setSwapOption(0, {"from": owner})
    alice_initial_balance = cvxfxs_lp_balance(alice)
    vault.depositAll(alice, {"from": alice})
    chain.sleep(100000)
    chain.mine(1)
    harvested = estimate_lp_tokens_received(calc_harvest_amount_curve(strategy))

    tx = vault.withdrawAll(alice, {"from": alice})
    assert approx(
        cvxfxs_lp_balance(alice), alice_initial_balance + harvested, 1e-3
    )  # harvest as last to claim
    assert (
        cvxfxs_lp_balance(alice)
        == alice_initial_balance + tx.events["Harvest"]["_value"]
    )
    assert (
        interface.IBasicRewards(CVXFXS_STAKING_CONTRACT).balanceOf(strategy) == 0
    )  # last to claim == all withdrawn
    assert vault.balanceOf(alice) == 0
    chain.revert()
