import brownie
import pytest
from brownie import chain, interface

from ....utils import cvxfxs_lp_balance
from ....utils.constants import CVXCRV, CVXFXS_STAKING_CONTRACT


def test_deposit(alice, owner, vault, strategy):
    chain.snapshot()

    alice_initial_lp_balance = cvxfxs_lp_balance(alice)
    amount = 1e22
    tx = vault.deposit(alice, amount, {"from": alice})
    assert cvxfxs_lp_balance(vault) == 0
    assert cvxfxs_lp_balance(strategy) == 0
    assert cvxfxs_lp_balance(alice) == alice_initial_lp_balance - amount
    assert vault.balanceOf(alice) == amount
    assert vault.totalUnderlying() == amount
    assert interface.IBasicRewards(CVXFXS_STAKING_CONTRACT).balanceOf(strategy) == amount

    assert tx.events["Staked"]['user'] == strategy
    assert tx.events["Staked"]['amount'] == amount
    chain.revert()


def test_deposit_null_value(alice, strategy, vault):
    with brownie.reverts("Deposit too small"):
        vault.deposit(alice, 0, {"from": alice})


@pytest.mark.parametrize("amount", [100, 1e20])
def test_multiple_deposit(accounts, vault, strategy, amount):
    chain.snapshot()
    for i, account in enumerate(accounts[:10]):
        account_initial_balance = cvxfxs_lp_balance(account)
        vault.deposit(account, amount, {"from": account})

        assert cvxfxs_lp_balance(account) == account_initial_balance - amount
        assert interface.IBasicRewards(CVXFXS_STAKING_CONTRACT).balanceOf(strategy) == amount * (
            i + 1
        )
        assert vault.balanceOf(account) == amount

    chain.revert()


def test_deposit_all(alice, vault, strategy):
    chain.snapshot()
    alice_initial_balance = cvxfxs_lp_balance(alice)
    vault.depositAll(alice, {"from": alice})

    assert cvxfxs_lp_balance(alice) == 0
    assert (
        interface.IBasicRewards(CVXFXS_STAKING_CONTRACT).balanceOf(strategy)
        == alice_initial_balance
    )
    assert vault.balanceOf(alice) == alice_initial_balance
    chain.revert()


def test_deposit_no_lp_token(alice, vault, strategy):
    with brownie.reverts():
        vault.deposit(alice, 1e22, {"from": CVXCRV})