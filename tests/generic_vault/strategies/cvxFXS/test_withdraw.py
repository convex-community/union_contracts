import brownie
import pytest
from brownie import interface, chain
from decimal import Decimal

from ....utils.constants import CVXCRV_REWARDS, CVXFXS_STAKING_CONTRACT
from ....utils import approx, cvxfxs_lp_balance


@pytest.mark.parametrize("amount", [1e20])
def test_unique_partial_withdrawal(alice, owner, vault, strategy, amount):
    chain.snapshot()
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
        interface.IBasicRewards(CVXFXS_STAKING_CONTRACT).balanceOf(vault),
        half_amount + penalty_amount,
        1e-18,
    )
    assert approx(tx.events["Withdraw"]["_value"], half_amount - penalty_amount, 1e-18)
    assert tx.events["Withdraw"]["_from"] == alice
    assert tx.events["Withdraw"]["_to"] == alice
    assert approx(vault.balanceOf(alice), half_amount, 1e-18)
    chain.revert()
