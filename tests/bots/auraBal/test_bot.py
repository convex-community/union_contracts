from decimal import Decimal

import pytest
import brownie
from brownie import chain, Contract

from tests.utils import approx
from tests.utils.aurabal import (
    calc_harvest_amount_aura,
    get_aurabal_to_lptoken_amount,
    estimate_underlying_received_baleth,
)


@pytest.mark.parametrize("lock", [False, True])
def test_harvest(owner, bot, strategy, vault, lock, fn_isolation):
    initial_balance = owner.balance()
    estimated_harvested_aurabal = calc_harvest_amount_aura(strategy, lock)

    call_incentive = Decimal(vault.callIncentive()) / 10000
    lp_token_amount = get_aurabal_to_lptoken_amount(
        int(estimated_harvested_aurabal * call_incentive)
    )
    eth_amount = estimate_underlying_received_baleth(strategy, lp_token_amount, 1)

    tx = bot.harvest(0, lock, {"from": owner})

    assert approx(owner.balance(), initial_balance + eth_amount, 1e-3)


@pytest.mark.skip(reason="crashes brownie")
@pytest.mark.parametrize("lock", [False, True])
def test_harvest_slippage(owner, bot, strategy, vault, lock, fn_isolation):
    initial_balance = owner.balance()
    estimated_harvested_aurabal = calc_harvest_amount_aura(strategy, lock)

    call_incentive = Decimal(vault.callIncentive()) / 10000
    lp_token_amount = get_aurabal_to_lptoken_amount(
        int(estimated_harvested_aurabal * call_incentive)
    )
    eth_amount = estimate_underlying_received_baleth(strategy, lp_token_amount, 1)

    with brownie.reverts():
        bot.harvest(int(eth_amount * 1.2), lock, {"from": owner})


def test_harvest_non_authorized(alice, bot, fn_isolation):
    with brownie.reverts():
        bot.harvest(0, True, {"from": alice})


def test_change_owner_non_authorized(alice, bot, fn_isolation):
    with brownie.reverts():
        bot.change_owner(alice, {"from": alice})


def test_change_owner(owner, alice, bot, fn_isolation):
    bot.change_owner(alice, {"from": owner})
    assert bot.owner() == alice


def test_update_authorized_caller_non_authorized(alice, bot, fn_isolation):
    with brownie.reverts():
        bot.update_authorized_caller(alice, True, {"from": alice})


def test_update_authorized_caller(owner, alice, bot, fn_isolation):
    assert bot.authorized_callers(alice) == False
    bot.update_authorized_caller(alice, True, {"from": owner})
    assert bot.authorized_callers(alice) == True
    bot.update_authorized_caller(alice, False, {"from": owner})
    assert bot.authorized_callers(alice) == False
