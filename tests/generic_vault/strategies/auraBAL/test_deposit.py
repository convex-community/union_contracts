import brownie
import pytest
from brownie import chain, interface

from ....utils import aurabal_balance
from ....utils.constants import CVXCRV, AURA_BAL_STAKING


def test_deposit(fn_isolation, alice, owner, vault, strategy):

    alice_initial_balance = aurabal_balance(alice)
    amount = 5e21
    tx = vault.deposit(alice, amount, {"from": alice})
    assert aurabal_balance(vault) == 0
    assert aurabal_balance(strategy) == 0
    assert aurabal_balance(alice) == alice_initial_balance - amount
    assert vault.balanceOf(alice) == amount
    assert vault.totalUnderlying() == amount
    assert interface.IBasicRewards(AURA_BAL_STAKING).balanceOf(strategy) == amount


def test_deposit_null_value(alice, strategy, vault):
    with brownie.reverts("Deposit too small"):
        vault.deposit(alice, 0, {"from": alice})


@pytest.mark.parametrize("amount", [100, 1e20])
def test_multiple_deposit(fn_isolation, accounts, vault, strategy, amount):
    for i, account in enumerate(accounts[:10]):
        account_initial_balance = aurabal_balance(account)
        vault.deposit(account, amount, {"from": account})

        assert aurabal_balance(account) == account_initial_balance - amount
        assert interface.IBasicRewards(AURA_BAL_STAKING).balanceOf(
            strategy
        ) == amount * (i + 1)
        assert vault.balanceOf(account) == amount


def test_deposit_all(fn_isolation, alice, vault, strategy):
    alice_initial_balance = aurabal_balance(alice)
    vault.depositAll(alice, {"from": alice})

    assert aurabal_balance(alice) == 0
    assert (
        interface.IBasicRewards(AURA_BAL_STAKING).balanceOf(strategy)
        == alice_initial_balance
    )
    assert vault.balanceOf(alice) == alice_initial_balance


def test_deposit_no_lp_token(alice, vault, strategy):
    with brownie.reverts():
        vault.deposit(alice, 1e22, {"from": CVXCRV})
