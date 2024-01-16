from brownie import interface, chain
import pytest
from ....utils import approx, cvxprisma_balance, PRISMA
from ....utils.constants import CURVE_CVXPRISMA_PRISMA_POOL, PRISMA_LOCKER
from ....utils.cvxprisma import calc_staking_harvest_amount


def test_harvest_single_staker(
    fn_isolation, alice, bob, owner, vault, strategy, staking, harvester
):
    harvester.setApprovals({"from": owner})
    alice_initial_balance = cvxprisma_balance(alice)
    bob_initial_balance = cvxprisma_balance(bob)
    platform_initial_balance = cvxprisma_balance(vault.platform())
    vault.depositAll(alice, {"from": alice})
    chain.sleep(60 * 60 * 24 * 30)
    chain.mine(1)
    gross_estimated_harvest = calc_staking_harvest_amount(strategy, staking)
    print(gross_estimated_harvest)
    print("\033[95m" + f"Harvested: {str(gross_estimated_harvest * 1e-18)} PRISMA")
    print("=" * 32 + "\033[0m")
    platform_fees = gross_estimated_harvest * vault.platformFee() // 10000
    caller_incentive = gross_estimated_harvest * vault.callIncentive() // 10000

    net_harvest = gross_estimated_harvest - platform_fees - caller_incentive

    tx = vault.harvest({"from": bob})

    actual_harvest = tx.events["Harvest"]["_value"]

    assert approx(net_harvest, actual_harvest, 1e-3)
    assert approx(cvxprisma_balance(bob), bob_initial_balance + caller_incentive, 1e-5)
    assert approx(
        cvxprisma_balance(vault.platform()),
        platform_initial_balance + platform_fees,
        1e-5,
    )
    assert approx(
        staking.balanceOf(strategy),
        alice_initial_balance + net_harvest,
        1e-5,
    )
    assert approx(
        vault.balanceOfUnderlying(alice),
        alice_initial_balance + net_harvest,
        1e-5,
    )


def test_harvest_multiple_stakers(
    fn_isolation,
    alice,
    bob,
    charlie,
    dave,
    erin,
    owner,
    vault,
    strategy,
    staking,
    harvester,
):
    initial_balances = {}
    accounts = [alice, bob, charlie, dave, erin]

    for account in accounts:
        initial_balances[account.address] = cvxprisma_balance(account)
        vault.depositAll(account, {"from": account})

    bob_initial_balance = cvxprisma_balance(bob)
    initial_vault_balance = vault.totalUnderlying()
    platform_initial_balance = cvxprisma_balance(vault.platform())
    chain.sleep(60 * 60 * 24 * 30)
    chain.mine(1)
    gross_estimated_harvest = calc_staking_harvest_amount(strategy, staking)
    print("\033[95m" + f"Harvested: {gross_estimated_harvest * 1e-18} PRISMA")
    print("=" * 32 + "\033[0m")
    platform_fees = gross_estimated_harvest * vault.platformFee() // 10000
    caller_incentive = gross_estimated_harvest * vault.callIncentive() // 10000

    net_harvest = gross_estimated_harvest - platform_fees - caller_incentive

    tx = vault.harvest({"from": bob})

    actual_harvest = tx.events["Harvest"]["_value"]

    assert approx(net_harvest, actual_harvest, 1e-3)
    assert approx(cvxprisma_balance(bob), bob_initial_balance + caller_incentive, 1e-5)
    assert approx(
        cvxprisma_balance(vault.platform()),
        platform_initial_balance + platform_fees,
        1e-5,
    )
    assert approx(
        vault.totalUnderlying(),
        initial_vault_balance + net_harvest,
        1e-5,
    )
    assert approx(
        vault.balanceOfUnderlying(account) - initial_balances[account.address],
        (net_harvest) // len(accounts),
        1e-5,
    )


def test_harvest_with_harvester_change(
    fn_isolation,
    alice,
    bob,
    charlie,
    dave,
    erin,
    owner,
    vault,
    strategy,
    staking,
    second_harvester,
):
    strategy.setHarvester(second_harvester, {"from": owner})
    initial_balances = {}
    accounts = [alice, bob, charlie, dave, erin]

    for account in accounts:
        initial_balances[account.address] = cvxprisma_balance(account)
        vault.depositAll(account, {"from": account})

    bob_initial_balance = cvxprisma_balance(bob)
    initial_vault_balance = vault.totalUnderlying()
    platform_initial_balance = cvxprisma_balance(vault.platform())
    chain.sleep(60 * 60 * 24 * 30)
    chain.mine(1)
    gross_estimated_harvest = calc_staking_harvest_amount(strategy, staking)
    print("\033[95m" + f"Harvested: {gross_estimated_harvest * 1e-18} PRISMA")
    print("=" * 32 + "\033[0m")
    platform_fees = gross_estimated_harvest * vault.platformFee() // 10000
    caller_incentive = gross_estimated_harvest * vault.callIncentive() // 10000

    net_harvest = gross_estimated_harvest - platform_fees - caller_incentive

    tx = vault.harvest({"from": bob})

    actual_harvest = tx.events["Harvest"]["_value"]

    assert approx(net_harvest, actual_harvest, 1e-3)
    assert approx(cvxprisma_balance(bob), bob_initial_balance + caller_incentive, 1e-5)
    assert approx(
        cvxprisma_balance(vault.platform()),
        platform_initial_balance + platform_fees,
        1e-5,
    )
    assert approx(
        vault.totalUnderlying(),
        initial_vault_balance + net_harvest,
        1e-5,
    )
    assert approx(
        vault.balanceOfUnderlying(account) - initial_balances[account.address],
        (net_harvest) // len(accounts),
        1e-5,
    )


def test_harvest_with_discount(
    fn_isolation,
    alice,
    bob,
    charlie,
    dave,
    erin,
    owner,
    vault,
    strategy,
    staking,
    harvester,
):
    initial_balances = {}

    prisma = interface.IERC20(PRISMA)
    prisma.approve(CURVE_CVXPRISMA_PRISMA_POOL, 2**256 - 1, {"from": PRISMA_LOCKER})
    cvxprisma_swap = interface.ICurveV2Pool(CURVE_CVXPRISMA_PRISMA_POOL)
    print(f"Price oracle before {cvxprisma_swap.price_oracle()}")
    total_liq = prisma.balanceOf(PRISMA_LOCKER)
    steps = 5
    for i in range(steps):
        cvxprisma_swap.add_liquidity(
            [total_liq // steps, 0],
            0,
            {"from": PRISMA_LOCKER},
        )
        chain.sleep(10000)
        chain.mine(1)
    print(f"Price oracle after {cvxprisma_swap.price_oracle()}")

    accounts = [alice, bob, charlie, dave, erin]

    for account in accounts:
        initial_balances[account.address] = cvxprisma_balance(account)
        vault.depositAll(account, {"from": account})

    bob_initial_balance = cvxprisma_balance(bob)
    initial_vault_balance = vault.totalUnderlying()
    platform_initial_balance = cvxprisma_balance(vault.platform())
    chain.sleep(60 * 60 * 24 * 30)
    chain.mine(1)
    gross_estimated_harvest = calc_staking_harvest_amount(strategy, staking, True)
    print("\033[95m" + f"Harvested: {gross_estimated_harvest * 1e-18} PRISMA")
    print("=" * 32 + "\033[0m")
    platform_fees = gross_estimated_harvest * vault.platformFee() // 10000
    caller_incentive = gross_estimated_harvest * vault.callIncentive() // 10000

    net_harvest = gross_estimated_harvest - platform_fees - caller_incentive

    tx = vault.harvest({"from": bob})

    actual_harvest = tx.events["Harvest"]["_value"]

    assert approx(net_harvest, actual_harvest, 1e-3)
    assert approx(cvxprisma_balance(bob), bob_initial_balance + caller_incentive, 1e-5)
    assert approx(
        cvxprisma_balance(vault.platform()),
        platform_initial_balance + platform_fees,
        1e-5,
    )
    assert approx(
        vault.totalUnderlying(),
        initial_vault_balance + net_harvest,
        1e-5,
    )
    assert approx(
        vault.balanceOfUnderlying(account) - initial_balances[account.address],
        (net_harvest) // len(accounts),
        1e-5,
    )
