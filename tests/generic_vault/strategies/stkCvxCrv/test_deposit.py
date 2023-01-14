import brownie
import pytest
from brownie import interface, chain

from ....utils.constants import CVXCRV, CVXCRV_REWARDS
from ....utils import cvxcrv_balance


@pytest.mark.parametrize("amount", [1e20])
def test_unique_deposit(alice, vault, wrapper, strategy, amount):
    chain.snapshot()
    alice_initial_balance = cvxcrv_balance(alice)
    tx = vault.deposit(alice, amount, {"from": alice})

    assert cvxcrv_balance(vault) == 0
    assert cvxcrv_balance(alice) == alice_initial_balance - amount
    assert interface.ICvxCrvStaking(wrapper).balanceOf(strategy) == amount
    assert tx.events["Deposit"]["_value"] == amount
    assert tx.events["Deposit"]["_from"] == alice
    assert tx.events["Deposit"]["_to"] == alice
    assert vault.balanceOf(alice) == amount
    chain.revert()


def test_deposit_null_value(alice, vault):
    with brownie.reverts("Deposit too small"):
        vault.deposit(alice, 0, {"from": alice})


@pytest.mark.parametrize("amount", [100, 1e20])
def test_multiple_deposit(accounts, vault, amount, wrapper, strategy):
    chain.snapshot()
    for i, account in enumerate(accounts[:4]):
        account_initial_balance = cvxcrv_balance(account)
        vault.deposit(account, amount, {"from": account})

        assert cvxcrv_balance(account) == account_initial_balance - amount
        assert interface.ICvxCrvStaking(wrapper).balanceOf(strategy) == amount * (
            i + 1
        )
        assert vault.balanceOf(account) == amount

    chain.revert()


def test_deposit_all(alice, vault, wrapper, strategy):
    chain.snapshot()
    alice_initial_balance = cvxcrv_balance(alice)
    vault.depositAll(alice, {"from": alice})

    assert cvxcrv_balance(alice) == 0
    assert (
        interface.ICvxCrvStaking(wrapper).balanceOf(strategy)
        == alice_initial_balance
    )
    assert vault.balanceOf(alice) == alice_initial_balance
    chain.revert()
