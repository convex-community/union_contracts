import pytest
import brownie
from brownie import chain, Contract


def test_harvest(owner, bot, fn_isolation):
    initial_balance = owner.balance()
    bot.harvest(0, True, {"from": owner})
    assert owner.balance() > initial_balance
