import brownie
import pytest

from ....utils import cvxprisma_balance
from ....utils.constants import CVXCRV


def test_deposit(fn_isolation, alice, owner, vault, strategy, staking):

    alice_initial_cvxprisma_balance = cvxprisma_balance(alice)
    amount = 1e21
    tx = vault.deposit(alice, amount, {"from": alice})
    assert cvxprisma_balance(vault) == 0
    assert cvxprisma_balance(strategy) == 0
    assert cvxprisma_balance(alice) == alice_initial_cvxprisma_balance - amount
    assert vault.balanceOf(alice) == amount
    assert vault.totalUnderlying() == amount
    assert staking.balanceOf(strategy) == amount


def test_deposit_null_value(alice, strategy, vault):
    with brownie.reverts("Deposit too small"):
        vault.deposit(alice, 0, {"from": alice})


@pytest.mark.parametrize("amount", [100, 1e20])
def test_multiple_deposit(fn_isolation, accounts, vault, strategy, amount, staking):
    for i, account in enumerate(accounts[:10]):
        account_initial_balance = cvxprisma_balance(account)
        vault.deposit(account, amount, {"from": account})

        assert cvxprisma_balance(account) == account_initial_balance - amount
        assert staking.balanceOf(strategy) == amount * (i + 1)
        assert vault.balanceOf(account) == amount


def test_deposit_all(fn_isolation, alice, vault, strategy, staking):
    alice_initial_balance = cvxprisma_balance(alice)
    vault.depositAll(alice, {"from": alice})

    assert cvxprisma_balance(alice) == 0
    assert staking.balanceOf(strategy) == alice_initial_balance
    assert vault.balanceOf(alice) == alice_initial_balance


def test_deposit_no_lp_token(alice, vault, strategy):
    with brownie.reverts():
        vault.deposit(alice, 1e21, {"from": CVXCRV})
