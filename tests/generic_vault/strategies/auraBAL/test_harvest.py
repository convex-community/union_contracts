from brownie import interface, chain
import pytest
import brownie
from ....utils.constants import AURA_BAL_STAKING
from ....utils import approx, aurabal_balance
from ....utils.aurabal import calc_harvest_amount_aura


@pytest.mark.parametrize("lock", [False, True])
def test_harvest_single_staker(fn_isolation, alice, bob, owner, vault, strategy, lock):
    alice_initial_balance = aurabal_balance(alice)
    bob_initial_balance = aurabal_balance(bob)
    platform_initial_balance = aurabal_balance(vault.platform())
    vault.depositAll(alice, {"from": alice})
    chain.sleep(60 * 60 * 24 * 30)
    chain.mine(1)

    estimated_harvested_aurabal = calc_harvest_amount_aura(strategy, lock)
    print(f"Harvested: {estimated_harvested_aurabal} auraBAL (lock: {lock})")

    platform_fees = estimated_harvested_aurabal * vault.platformFee() // 10000
    caller_incentive = estimated_harvested_aurabal * vault.callIncentive() // 10000

    estimated_harvest = estimated_harvested_aurabal - platform_fees - caller_incentive

    # with brownie.reverts("slippage"):
    #    vault.harvest(estimated_harvest * 2, {"from": bob})

    tx = vault.harvest(0, lock, {"from": bob})

    actual_harvest = tx.events["Harvest"]["_value"]

    assert approx(estimated_harvest, actual_harvest, 3e-3)
    assert approx(aurabal_balance(bob), bob_initial_balance + caller_incentive, 3e-3)
    assert approx(
        aurabal_balance(vault.platform()),
        platform_initial_balance + platform_fees,
        3e-3,
    )
    assert approx(
        interface.IBasicRewards(AURA_BAL_STAKING).balanceOf(strategy),
        alice_initial_balance + estimated_harvest,
        3e-3,
    )
    assert approx(
        vault.balanceOfUnderlying(alice),
        alice_initial_balance + estimated_harvest,
        3e-3,
    )


@pytest.mark.parametrize("lock", [True, False])
def test_harvest_multiple_stakers(
    fn_isolation, alice, bob, charlie, dave, erin, owner, vault, strategy, lock
):
    initial_balances = {}
    accounts = [alice, bob, charlie, dave, erin]

    for account in accounts:
        initial_balances[account.address] = aurabal_balance(account)
        vault.depositAll(account, {"from": account})

    bob_initial_balance = aurabal_balance(bob)
    platform_initial_balance = aurabal_balance(vault.platform())
    initial_vault_balance = vault.totalUnderlying()

    chain.sleep(60 * 60 * 24 * 30)
    chain.mine(1)

    estimated_harvested_aurabal = calc_harvest_amount_aura(strategy, lock)
    print(f"Harvested: {estimated_harvested_aurabal} auraBAL (lock: {lock})")

    platform_fees = estimated_harvested_aurabal * vault.platformFee() // 10000
    caller_incentive = estimated_harvested_aurabal * vault.callIncentive() // 10000

    estimated_harvest = estimated_harvested_aurabal - platform_fees - caller_incentive

    with brownie.reverts("slippage"):
        vault.harvest(estimated_harvest * 2, {"from": bob})

    tx = vault.harvest(0, lock, {"from": bob})

    actual_harvest = tx.events["Harvest"]["_value"]
    assert approx(estimated_harvest, actual_harvest, 3e-3)

    assert approx(aurabal_balance(bob), bob_initial_balance + caller_incentive, 3e-3)
    assert approx(
        aurabal_balance(vault.platform()),
        platform_initial_balance + platform_fees,
        3e-3,
    )
    assert approx(
        vault.totalUnderlying(),
        initial_vault_balance + estimated_harvest,
        3e-3,
    )
    for account in accounts:
        assert approx(
            vault.balanceOfUnderlying(account) - initial_balances[account.address],
            (estimated_harvest) // len(accounts),
            3e-3,
        )
