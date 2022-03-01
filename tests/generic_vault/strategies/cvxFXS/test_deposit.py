import brownie
from brownie import chain, interface

from ....utils.constants import CURVE_CVXFXS_FXS_LP_TOKEN, CVXFXS_STAKING_CONTRACT


def test_deposit(alice, owner, vault, strategy):
    chain.snapshot()
    curve_lp_token = interface.IERC20(CURVE_CVXFXS_FXS_LP_TOKEN)
    alice_initial_lp_balance = curve_lp_token.balanceOf(alice)
    amount = 1e22
    tx = vault.deposit(alice, amount, {"from": alice})
    assert curve_lp_token.balanceOf(vault) == 0
    assert curve_lp_token.balanceOf(strategy) == 0
    assert curve_lp_token.balanceOf(alice) == alice_initial_lp_balance - amount
    assert vault.balanceOf(alice) == amount
    assert vault.totalUnderlying() == amount
    assert interface.IBasicRewards(CVXFXS_STAKING_CONTRACT).balanceOf(strategy) == amount

    assert tx.events["Staked"].user == strategy
    assert tx.events["Staked"].amount == amount
    assert tx.events["Deposit"]._value == amount
    assert tx.events["Deposit"]._to == alice
    chain.revert()