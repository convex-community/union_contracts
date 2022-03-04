from brownie import interface, chain
import pytest
from ....utils.constants import CVXFXS_STAKING_CONTRACT
from ....utils import approx, cvxfxs_lp_balance, fxs_balance
from ....utils.cvxfxs import (
    calc_harvest_amount_curve,
    estimate_lp_tokens_received,
    calc_harvest_amount_uniswap,
    calc_harvest_amount_unistable,
)


@pytest.mark.parametrize("option", [0, 1, 2])
def test_harvest_single_staker(alice, bob, owner, vault, strategy, option):
    chain.snapshot()
    strategy.setSwapOption(option, {"from": owner})
    alice_initial_balance = cvxfxs_lp_balance(alice)
    bob_initial_balance = fxs_balance(bob)
    platform_initial_balance = fxs_balance(vault.platform())
    vault.depositAll(alice, {"from": alice})
    chain.sleep(60 * 60 * 24 * 30)
    chain.mine(1)
    if option == 0:
        estimated_harvested_fxs = calc_harvest_amount_curve(strategy)
        print(f"Harvested Curve: {estimated_harvested_fxs} FXS")
    elif option == 1:
        estimated_harvested_fxs = calc_harvest_amount_uniswap(strategy)
        print(f"Harvested UniV3: {estimated_harvested_fxs} FXS")
    else:
        estimated_harvested_fxs = calc_harvest_amount_unistable(strategy)
        print(f"Harvested UniStable: {estimated_harvested_fxs} FXS")

    platform_fees = estimated_harvested_fxs * vault.platformFee() // 10000
    caller_incentive = estimated_harvested_fxs * vault.callIncentive() // 10000

    estimated_harvest = estimate_lp_tokens_received(
        estimated_harvested_fxs - platform_fees - caller_incentive
    )
    tx = vault.harvest({"from": bob})

    actual_harvest = tx.events["Harvest"]["_value"]

    assert approx(estimated_harvest, actual_harvest, 1e-3)
    assert approx(fxs_balance(bob), bob_initial_balance + caller_incentive, 1e-5)
    assert approx(
        fxs_balance(vault.platform()), platform_initial_balance + platform_fees, 1e-5
    )
    assert approx(
        interface.IBasicRewards(CVXFXS_STAKING_CONTRACT).balanceOf(strategy),
        alice_initial_balance + estimated_harvest,
        1e-5,
    )
    assert approx(
        vault.balanceOfUnderlying(alice),
        alice_initial_balance + estimated_harvest,
        1e-5,
    )
    chain.revert()


@pytest.mark.parametrize("option", [0, 1, 2])
def test_harvest_multiple_stakers(
    alice, bob, charlie, dave, erin, owner, vault, strategy, option
):
    chain.snapshot()
    strategy.setSwapOption(option, {"from": owner})
    initial_balances = {}
    accounts = [alice, bob, charlie, dave, erin]

    for account in accounts:
        initial_balances[account.address] = cvxfxs_lp_balance(account)
        vault.depositAll(account, {"from": account})

    bob_initial_balance = fxs_balance(bob)
    platform_initial_balance = fxs_balance(vault.platform())
    initial_vault_balance = vault.totalUnderlying()

    chain.sleep(60 * 60 * 24 * 30)
    chain.mine(1)

    if option == 0:
        estimated_harvested_fxs = calc_harvest_amount_curve(strategy)
        print(f"Harvested Curve: {estimated_harvested_fxs} FXS")
    elif option == 1:
        estimated_harvested_fxs = calc_harvest_amount_uniswap(strategy)
        print(f"Harvested UniV3: {estimated_harvested_fxs} FXS")
    else:
        estimated_harvested_fxs = calc_harvest_amount_unistable(strategy)
        print(f"Harvested UniStable: {estimated_harvested_fxs} FXS")

    platform_fees = estimated_harvested_fxs * vault.platformFee() // 10000
    caller_incentive = estimated_harvested_fxs * vault.callIncentive() // 10000

    estimated_harvest = estimate_lp_tokens_received(
        estimated_harvested_fxs - platform_fees - caller_incentive
    )

    tx = vault.harvest({"from": bob})

    actual_harvest = tx.events["Harvest"]["_value"]
    assert approx(estimated_harvest, actual_harvest, 1e-3)

    assert approx(fxs_balance(bob), bob_initial_balance + caller_incentive, 1e-5)
    assert approx(
        fxs_balance(vault.platform()), platform_initial_balance + platform_fees, 1e-5
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
    chain.revert()
