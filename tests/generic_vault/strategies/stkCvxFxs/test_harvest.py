from brownie import interface, chain
import pytest
from ....utils import approx, cvxfxs_balance, FXS
from ....utils.constants import CURVE_CVXFXS_FXS_POOL, FXS_VOTING_ESCROW
from ....utils.cvxfxs import calc_staking_harvest_amount

OPTIONS = ["Curve", "UniV3EthToFxs", "UniV3EthFraxFxs", "UniCurveEthFraxUsdcFxs"]


@pytest.mark.parametrize("option", [0, 1, 2, 3])
def test_harvest_single_staker(
    fn_isolation, alice, bob, owner, vault, strategy, staking, option, harvester
):
    harvester.setSwapOption(option, {"from": owner})
    alice_initial_balance = cvxfxs_balance(alice)
    bob_initial_balance = cvxfxs_balance(bob)
    platform_initial_balance = cvxfxs_balance(vault.platform())
    vault.depositAll(alice, {"from": alice})
    chain.sleep(60 * 60 * 24 * 30)
    chain.mine(1)
    gross_estimated_harvest = calc_staking_harvest_amount(strategy, staking, option)
    print(
        "\033[95m"
        + f"Harvested {OPTIONS[option]}: {gross_estimated_harvest * 1e-18} FXS"
    )
    print("=" * 32 + "\033[0m")
    platform_fees = gross_estimated_harvest * vault.platformFee() // 10000
    caller_incentive = gross_estimated_harvest * vault.callIncentive() // 10000

    net_harvest = gross_estimated_harvest - platform_fees - caller_incentive

    tx = vault.harvest({"from": bob})

    actual_harvest = tx.events["Harvest"]["_value"]

    assert approx(net_harvest, actual_harvest, 1e-3)
    assert approx(cvxfxs_balance(bob), bob_initial_balance + caller_incentive, 1e-5)
    assert approx(
        cvxfxs_balance(vault.platform()), platform_initial_balance + platform_fees, 1e-5
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


@pytest.mark.parametrize("option", [0, 1, 2, 3])
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
    option,
    harvester,
):
    harvester.setSwapOption(option, {"from": owner})
    initial_balances = {}
    accounts = [alice, bob, charlie, dave, erin]

    for account in accounts:
        initial_balances[account.address] = cvxfxs_balance(account)
        vault.depositAll(account, {"from": account})

    bob_initial_balance = cvxfxs_balance(bob)
    initial_vault_balance = vault.totalUnderlying()
    platform_initial_balance = cvxfxs_balance(vault.platform())
    chain.sleep(60 * 60 * 24 * 30)
    chain.mine(1)
    gross_estimated_harvest = calc_staking_harvest_amount(strategy, staking, option)
    print(
        "\033[95m"
        + f"Harvested {OPTIONS[option]}: {gross_estimated_harvest * 1e-18} FXS"
    )
    print("=" * 32 + "\033[0m")
    platform_fees = gross_estimated_harvest * vault.platformFee() // 10000
    caller_incentive = gross_estimated_harvest * vault.callIncentive() // 10000

    net_harvest = gross_estimated_harvest - platform_fees - caller_incentive

    tx = vault.harvest({"from": bob})

    actual_harvest = tx.events["Harvest"]["_value"]

    assert approx(net_harvest, actual_harvest, 1e-3)
    assert approx(cvxfxs_balance(bob), bob_initial_balance + caller_incentive, 1e-5)
    assert approx(
        cvxfxs_balance(vault.platform()), platform_initial_balance + platform_fees, 1e-5
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


@pytest.mark.parametrize("option", [0, 1, 2, 3])
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
    option,
    second_harvester,
):
    second_harvester.setSwapOption(option, {"from": owner})
    strategy.setHarvester(second_harvester, {"from": owner})
    initial_balances = {}
    accounts = [alice, bob, charlie, dave, erin]

    for account in accounts:
        initial_balances[account.address] = cvxfxs_balance(account)
        vault.depositAll(account, {"from": account})

    bob_initial_balance = cvxfxs_balance(bob)
    initial_vault_balance = vault.totalUnderlying()
    platform_initial_balance = cvxfxs_balance(vault.platform())
    chain.sleep(60 * 60 * 24 * 30)
    chain.mine(1)
    gross_estimated_harvest = calc_staking_harvest_amount(strategy, staking, option)
    print(
        "\033[95m"
        + f"Harvested {OPTIONS[option]}: {gross_estimated_harvest * 1e-18} FXS"
    )
    print("=" * 32 + "\033[0m")
    platform_fees = gross_estimated_harvest * vault.platformFee() // 10000
    caller_incentive = gross_estimated_harvest * vault.callIncentive() // 10000

    net_harvest = gross_estimated_harvest - platform_fees - caller_incentive

    tx = vault.harvest({"from": bob})

    actual_harvest = tx.events["Harvest"]["_value"]

    assert approx(net_harvest, actual_harvest, 1e-3)
    assert approx(cvxfxs_balance(bob), bob_initial_balance + caller_incentive, 1e-5)
    assert approx(
        cvxfxs_balance(vault.platform()), platform_initial_balance + platform_fees, 1e-5
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


@pytest.mark.parametrize("option", [0, 1, 2, 3])
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
    option,
    harvester,
):
    harvester.setSwapOption(option, {"from": owner})
    initial_balances = {}

    fxs = interface.IERC20(FXS)
    fxs.approve(CURVE_CVXFXS_FXS_POOL, 2**256 - 1, {"from": FXS_VOTING_ESCROW})
    cvxfxs_swap = interface.ICurveV2Pool(CURVE_CVXFXS_FXS_POOL)
    print(f"Price oracle before {cvxfxs_swap.price_oracle()}")
    total_liq = fxs.balanceOf(FXS_VOTING_ESCROW)
    steps = 5
    for i in range(steps):
        cvxfxs_swap.add_liquidity(
            [total_liq // steps, 0],
            0,
            {"from": FXS_VOTING_ESCROW},
        )
        chain.sleep(10000)
        chain.mine(1)
    print(f"Price oracle after {cvxfxs_swap.price_oracle()}")

    accounts = [alice, bob, charlie, dave, erin]

    for account in accounts:
        initial_balances[account.address] = cvxfxs_balance(account)
        vault.depositAll(account, {"from": account})

    bob_initial_balance = cvxfxs_balance(bob)
    initial_vault_balance = vault.totalUnderlying()
    platform_initial_balance = cvxfxs_balance(vault.platform())
    chain.sleep(60 * 60 * 24 * 30)
    chain.mine(1)
    gross_estimated_harvest = calc_staking_harvest_amount(
        strategy, staking, option, True
    )
    print(
        "\033[95m"
        + f"Harvested {OPTIONS[option]}: {gross_estimated_harvest * 1e-18} FXS"
    )
    print("=" * 32 + "\033[0m")
    platform_fees = gross_estimated_harvest * vault.platformFee() // 10000
    caller_incentive = gross_estimated_harvest * vault.callIncentive() // 10000

    net_harvest = gross_estimated_harvest - platform_fees - caller_incentive

    tx = vault.harvest({"from": bob})

    actual_harvest = tx.events["Harvest"]["_value"]

    assert approx(net_harvest, actual_harvest, 1e-3)
    assert approx(cvxfxs_balance(bob), bob_initial_balance + caller_incentive, 1e-5)
    assert approx(
        cvxfxs_balance(vault.platform()), platform_initial_balance + platform_fees, 1e-5
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
