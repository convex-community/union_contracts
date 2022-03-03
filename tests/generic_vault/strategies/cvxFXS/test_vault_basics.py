import brownie
from brownie import chain


def test_total_underlying(alice, bob, strategy, vault):
    chain.snapshot()
    vault.deposit(alice, 1e22, {"from": alice})
    assert vault.totalUnderlying() == 1e22
    vault.deposit(bob, 1e22, {"from": alice})
    assert vault.totalUnderlying() == 2e22
    chain.revert()
