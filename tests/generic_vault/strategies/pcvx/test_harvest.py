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


def test_harvest_single_staker(
    fn_isolation, alice, bob, owner, vault, pcvx, strategy, staking_rewards
):
    alice_initial_balance = pcvx.balanceOf(alice)
    bob_initial_balance = pcvx.balanceOf(bob)
    platform_initial_balance = pcvx.balanceOf(vault.platform())
    vault.depositAll(alice, {"from": alice})

    amount = 1e25
    pcvx.mint(owner, amount, {"from": owner})
    pcvx.transfer(staking_rewards, amount, {"from": owner})
    staking_rewards.notifyRewardAmount(amount, {"from": owner})
    chain.sleep(60 * 60 * 24 * 30)
    chain.mine(1)

    estimated_rewards = amount

    platform_fees = estimated_rewards * vault.platformFee() // 10000
    caller_incentive = estimated_rewards * vault.callIncentive() // 10000

    estimated_harvest = amount - platform_fees - caller_incentive

    tx = vault.harvest({"from": bob})

    actual_harvest = tx.events["Harvest"]["_value"]

    assert approx(estimated_harvest, actual_harvest, 1e-3)
    assert approx(pcvx.balanceOf(bob), bob_initial_balance + caller_incentive, 1e-5)
    assert approx(
        pcvx.balanceOf(vault.platform()), platform_initial_balance + platform_fees, 1e-5
    )
    assert approx(
        staking_rewards.balanceOf(strategy),
        alice_initial_balance + estimated_harvest,
        1e-5,
    )
    assert approx(
        vault.balanceOfUnderlying(alice),
        alice_initial_balance + estimated_harvest,
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
    staking_rewards,
    pcvx,
):
    initial_balances = {}
    accounts = [alice, bob, charlie, dave, erin]

    for account in accounts:
        initial_balances[account.address] = pcvx.balanceOf(account)
        vault.depositAll(account, {"from": account})

    bob_initial_balance = pcvx.balanceOf(bob)
    platform_initial_balance = pcvx.balanceOf(vault.platform())
    initial_vault_balance = vault.totalUnderlying()

    amount = 1e26
    pcvx.mint(owner, amount, {"from": owner})
    pcvx.transfer(staking_rewards, amount, {"from": owner})
    staking_rewards.notifyRewardAmount(amount, {"from": owner})

    chain.sleep(60 * 60 * 24 * 30)
    chain.mine(1)

    estimated_rewards = amount

    platform_fees = estimated_rewards * vault.platformFee() // 10000
    caller_incentive = estimated_rewards * vault.callIncentive() // 10000

    estimated_harvest = amount - platform_fees - caller_incentive

    tx = vault.harvest({"from": bob})

    actual_harvest = tx.events["Harvest"]["_value"]
    assert approx(estimated_harvest, actual_harvest, 1e-3)

    assert approx(pcvx.balanceOf(bob), bob_initial_balance + caller_incentive, 1e-5)
    assert approx(
        pcvx.balanceOf(vault.platform()), platform_initial_balance + platform_fees, 1e-5
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
