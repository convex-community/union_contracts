import brownie
import pytest
from brownie import chain, interface
from ....utils.constants import CVXCRV


def test_deposit(fn_isolation, alice, owner, vault, strategy, pcvx, staking_rewards):

    alice_initial_balance = pcvx.balanceOf(alice)
    amount = 1e22
    tx = vault.deposit(alice, amount, {"from": alice})
    assert pcvx.balanceOf(vault) == 0
    assert pcvx.balanceOf(strategy) == 0
    assert pcvx.balanceOf(alice) == alice_initial_balance - amount
    assert vault.balanceOf(alice) == amount
    assert vault.totalUnderlying() == amount
    assert staking_rewards.balanceOf(strategy) == amount


def test_deposit_null_value(alice, strategy, vault):
    with brownie.reverts("Deposit too small"):
        vault.deposit(alice, 0, {"from": alice})


@pytest.mark.parametrize("amount", [100, 1e20])
def test_multiple_deposit(
    fn_isolation, accounts, vault, strategy, pcvx, staking_rewards, amount
):
    for i, account in enumerate(accounts[:10]):
        account_initial_balance = pcvx.balanceOf(account)
        vault.deposit(account, amount, {"from": account})

        assert pcvx.balanceOf(account) == account_initial_balance - amount
        assert staking_rewards.balanceOf(strategy) == amount * (i + 1)
        assert vault.balanceOf(account) == amount


def test_deposit_all(fn_isolation, alice, vault, strategy, staking_rewards, pcvx):
    alice_initial_balance = pcvx.balanceOf(alice)
    vault.depositAll(alice, {"from": alice})

    assert pcvx.balanceOf(alice) == 0
    assert staking_rewards.balanceOf(strategy) == alice_initial_balance
    assert vault.balanceOf(alice) == alice_initial_balance


def test_deposit_no_lp_token(alice, vault, strategy):
    with brownie.reverts():
        vault.deposit(alice, 1e22, {"from": CVXCRV})
