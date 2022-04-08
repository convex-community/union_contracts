import brownie
import pytest
from brownie import interface, chain
from decimal import Decimal

from ....utils.constants import CVXFXS_STAKING_CONTRACT, ADDRESS_ZERO
from ....utils import approx, cvxfxs_lp_balance
from ....utils.cvxfxs import calc_harvest_amount_curve, estimate_lp_tokens_received


@pytest.mark.parametrize("amount", [1e20])
def test_unique_partial_withdrawal(
    fn_isolation, alice, owner, vault, strategy, pcvx, staking_rewards, amount
):
    alice_initial_balance = pcvx.balanceOf(alice)
    half_amount = int(Decimal(amount) / 2)
    vault.deposit(alice, amount, {"from": alice})
    tx = vault.withdraw(alice, half_amount, {"from": alice})
    penalty_amount = half_amount * vault.withdrawalPenalty() // 10000
    assert pcvx.balanceOf(vault) == 0
    assert approx(
        pcvx.balanceOf(alice),
        alice_initial_balance - half_amount - penalty_amount,
        1e-18,
    )
    assert approx(
        staking_rewards.balanceOf(strategy),
        half_amount + penalty_amount,
        1e-18,
    )
    assert approx(tx.events["Withdraw"]["_value"], half_amount - penalty_amount, 1e-18)
    assert approx(vault.balanceOf(alice), half_amount, 1e-18)


def test_withdraw_small(
    fn_isolation, alice, owner, strategy, vault, pcvx, staking_rewards
):
    alice_initial_balance = pcvx.balanceOf(alice)
    vault.deposit(alice, 1, {"from": alice})
    vault.withdrawAll(alice, {"from": alice})
    assert pcvx.balanceOf(alice) == alice_initial_balance  # no rewards
    assert staking_rewards.balanceOf(strategy) == 0
    assert vault.balanceOf(alice) == 0


def test_withdraw_address_zero(fn_isolation, alice, owner, vault):
    vault.depositAll(alice, {"from": alice})
    with brownie.reverts("Invalid address!"):
        vault.withdrawAll(ADDRESS_ZERO, {"from": alice})
    with brownie.reverts("Invalid address!"):
        vault.withdraw(ADDRESS_ZERO, 10, {"from": alice})


def test_withdraw_all(
    fn_isolation, alice, bob, owner, vault, strategy, staking_rewards, pcvx
):
    alice_initial_balance = pcvx.balanceOf(alice)
    vault.depositAll(alice, {"from": alice})

    amount = 1e26
    pcvx.mint(owner, amount, {"from": owner})
    pcvx.transfer(staking_rewards, amount, {"from": owner})
    staking_rewards.notifyRewardAmount(amount, {"from": owner})

    chain.sleep(60 * 60 * 24 * 30)
    chain.mine(1)

    tx = vault.withdrawAll(alice, {"from": alice})
    assert approx(
        pcvx.balanceOf(alice), alice_initial_balance + amount, 1e-3
    )  # harvest as last to claim
    assert (
        pcvx.balanceOf(alice) == alice_initial_balance + tx.events["Harvest"]["_value"]
    )
    assert staking_rewards.balanceOf(strategy) == 0  # last to claim == all withdrawn
    assert vault.balanceOf(alice) == 0
