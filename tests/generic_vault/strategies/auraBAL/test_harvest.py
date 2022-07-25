from brownie import interface, chain
import pytest
import brownie
from ....utils.constants import AURA_BAL_STAKING
from ....utils import approx, baleth_lp_balance, aurabal_balance
from ....utils.aurabal import calc_harvest_amount_aura


def test_harvest_single_staker(fn_isolation, alice, bob, owner, vault, strategy):
    alice_initial_balance = aurabal_balance(alice)
    bob_initial_balance = baleth_lp_balance(bob)
    platform_initial_balance = baleth_lp_balance(vault.platform())
    vault.depositAll(alice, {"from": alice})
    chain.sleep(60 * 60 * 24 * 30)
    chain.mine(1)

    estimated_harvested_baleth_lp = calc_harvest_amount_aura(strategy)
    print(f"Harvested: {estimated_harvested_baleth_lp} BALETH LP TOKEN")

    platform_fees = estimated_harvested_baleth_lp * vault.platformFee() // 10000
    caller_incentive = estimated_harvested_baleth_lp * vault.callIncentive() // 10000

    estimated_harvest = estimated_harvested_baleth_lp - platform_fees - caller_incentive

    with brownie.reverts("slippage"):
        vault.harvest(estimated_harvest * 2, {"from": bob})

    tx = vault.harvest({"from": bob})

    actual_harvest = tx.events["Harvest"]["_value"]

    assert approx(estimated_harvest, actual_harvest, 1e-3)
    assert approx(baleth_lp_balance(bob), bob_initial_balance + caller_incentive, 1e-5)
    assert approx(
        baleth_lp_balance(vault.platform()),
        platform_initial_balance + platform_fees,
        1e-5,
    )
    assert approx(
        interface.IBasicRewards(AURA_BAL_STAKING).balanceOf(strategy),
        alice_initial_balance + estimated_harvest,
        1e-5,
    )
    assert approx(
        vault.balanceOfUnderlying(alice),
        alice_initial_balance + estimated_harvest,
        1e-5,
    )


def test_harvest_multiple_stakers(
    fn_isolation, alice, bob, charlie, dave, erin, owner, vault, strategy
):
    initial_balances = {}
    accounts = [alice, bob, charlie, dave, erin]

    for account in accounts:
        initial_balances[account.address] = aurabal_balance(account)
        vault.depositAll(account, {"from": account})

    bob_initial_balance = baleth_lp_balance(bob)
    platform_initial_balance = baleth_lp_balance(vault.platform())
    initial_vault_balance = vault.totalUnderlying()

    chain.sleep(60 * 60 * 24 * 30)
    chain.mine(1)

    estimated_harvested_baleth_lp = calc_harvest_amount_aura(strategy)
    print(f"Harvested: {estimated_harvested_baleth_lp} BALETH LP Tokens")

    platform_fees = estimated_harvested_baleth_lp * vault.platformFee() // 10000
    caller_incentive = estimated_harvested_baleth_lp * vault.callIncentive() // 10000

    estimated_harvest = estimated_harvested_baleth_lp - platform_fees - caller_incentive

    with brownie.reverts("slippage"):
        vault.harvest(estimated_harvest * 2, {"from": bob})

    tx = vault.harvest({"from": bob})

    actual_harvest = tx.events["Harvest"]["_value"]
    assert approx(estimated_harvest, actual_harvest, 1e-3)

    assert approx(baleth_lp_balance(bob), bob_initial_balance + caller_incentive, 1e-5)
    assert approx(
        baleth_lp_balance(vault.platform()),
        platform_initial_balance + platform_fees,
        1e-5,
    )
    assert approx(
        vault.totalUnderlying(),
        initial_vault_balance + estimated_harvest,
        1e-5,
    )
    for account in accounts:
        assert approx(
            vault.balanceOfUnderlying(account) - initial_balances[account.address],
            (estimated_harvest) // len(accounts),
            1e5,
        )
