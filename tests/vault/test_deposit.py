import brownie
import pytest
from brownie import interface, chain

from ..utils.constants import CVXCRV, CVXCRV_REWARDS
from ..utils import cvxcrv_balance


@pytest.mark.parametrize("amount", [1e20])
def test_unique_deposit(alice, vault, amount):
    alice_initial_balance = cvxcrv_balance(alice)
    tx = vault.deposit(amount, {"from": alice})

    assert cvxcrv_balance(vault) == 0
    assert cvxcrv_balance(alice) == alice_initial_balance - amount
    assert interface.IBasicRewards(CVXCRV_REWARDS).balanceOf(vault) == amount
    assert tx.events["Stake"]["amount"] == amount
    assert vault.balanceOf(alice) == amount
    chain.undo()


def test_deposit_null_value(alice, vault):
    with brownie.reverts("Deposit too small"):
        vault.deposit(0, {"from": alice})


@pytest.mark.parametrize("amount", [100, 1e20])
def test_multiple_deposit(accounts, vault, amount):
    for i, account in enumerate(accounts[:10]):
        account_initial_balance = cvxcrv_balance(account)
        vault.deposit(amount, {"from": account})

        assert cvxcrv_balance(account) == account_initial_balance - amount
        assert interface.IBasicRewards(CVXCRV_REWARDS).balanceOf(vault) == amount * (
            i + 1
        )
        assert vault.balanceOf(account) == amount

    chain.undo(10)


def test_deposit_all(alice, vault):
    alice_initial_balance = cvxcrv_balance(alice)
    vault.depositAll({"from": alice})

    assert cvxcrv_balance(alice) == 0
    assert (
        interface.IBasicRewards(CVXCRV_REWARDS).balanceOf(vault)
        == alice_initial_balance
    )
    assert vault.balanceOf(alice) == alice_initial_balance
    chain.undo()
