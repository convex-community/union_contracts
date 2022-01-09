import brownie
import pytest
from brownie import interface, chain

from ..utils.constants import (
    CVXCRV_REWARDS,
    CRV,
    CURVE_CVXCRV_CRV_POOL,
    CURVE_VOTING_ESCROW,
)
from ..utils import approx, cvxcrv_balance, calc_harvest_amount_in_cvxcrv


def test_harvest_single_staker(alice, bob, owner, vault):
    chain.snapshot()
    alice_initial_balance = cvxcrv_balance(alice)
    bob_initial_balance = cvxcrv_balance(bob)
    platform_initial_balance = cvxcrv_balance(vault.platform())
    vault.setApprovals({"from": owner})
    vault.depositAll(alice, {"from": alice})
    chain.sleep(100000)
    chain.mine(1)
    estimated_harvest = calc_harvest_amount_in_cvxcrv(vault)
    tx = vault.harvest({"from": bob})

    actual_harvest = tx.events["Harvest"]["_value"]
    assert approx(estimated_harvest, actual_harvest, 1e-3)

    platform_fees = actual_harvest * vault.platformFee() // 10000
    caller_incentive = actual_harvest * vault.callIncentive() // 10000

    assert approx(cvxcrv_balance(bob), bob_initial_balance + caller_incentive, 1e-5)
    assert approx(
        cvxcrv_balance(vault.platform()), platform_initial_balance + platform_fees, 1e-5
    )
    assert approx(
        interface.IBasicRewards(CVXCRV_REWARDS).balanceOf(vault),
        alice_initial_balance + actual_harvest - platform_fees - caller_incentive,
        1e-5,
    )
    assert approx(
        vault.balanceOfUnderlying(alice),
        alice_initial_balance + actual_harvest - platform_fees - caller_incentive,
        1e-5,
    )
    chain.revert()


def test_harvest_no_discount(alice, bob, owner, vault):
    chain.snapshot()

    crv = interface.IERC20(CRV)
    crv.approve(CURVE_CVXCRV_CRV_POOL, 2 ** 256 - 1, {"from": CURVE_VOTING_ESCROW})
    cvxcrv_swap = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL)
    cvxcrv_swap.add_liquidity(
        [crv.balanceOf(CURVE_VOTING_ESCROW), 0],
        0,
        CURVE_VOTING_ESCROW,
        {"from": CURVE_VOTING_ESCROW},
    )

    alice_initial_balance = cvxcrv_balance(alice)
    bob_initial_balance = cvxcrv_balance(bob)
    platform_initial_balance = cvxcrv_balance(vault.platform())
    vault.setApprovals({"from": owner})
    vault.depositAll(alice, {"from": alice})
    chain.sleep(100000)
    chain.mine(1)
    estimated_harvest = calc_harvest_amount_in_cvxcrv(vault)
    tx = vault.harvest({"from": bob})

    actual_harvest = tx.events["Harvest"]["_value"]
    assert approx(estimated_harvest, actual_harvest, 1e-3)

    platform_fees = actual_harvest * vault.platformFee() // 10000
    caller_incentive = actual_harvest * vault.callIncentive() // 10000

    assert approx(cvxcrv_balance(bob), bob_initial_balance + caller_incentive, 1e-5)
    assert approx(
        cvxcrv_balance(vault.platform()), platform_initial_balance + platform_fees, 1e-5
    )
    assert approx(
        interface.IBasicRewards(CVXCRV_REWARDS).balanceOf(vault),
        alice_initial_balance + actual_harvest - platform_fees - caller_incentive,
        1e-5,
    )
    assert approx(
        vault.balanceOfUnderlying(alice),
        alice_initial_balance + actual_harvest - platform_fees - caller_incentive,
        1e-5,
    )
    chain.revert()


def test_harvest_multiple_stakers(alice, bob, charlie, dave, erin, owner, vault):
    chain.snapshot()
    initial_balances = {}
    accounts = [alice, bob, charlie, dave, erin]
    vault.setApprovals({"from": owner})

    for account in accounts:
        initial_balances[account.address] = cvxcrv_balance(account)
        vault.depositAll(account, {"from": account})

    platform_initial_balance = cvxcrv_balance(vault.platform())
    initial_vault_balance = vault.totalUnderlying()

    chain.sleep(100000)
    chain.mine(1)
    estimated_harvest = calc_harvest_amount_in_cvxcrv(vault)
    tx = vault.harvest({"from": bob})

    actual_harvest = tx.events["Harvest"]["_value"]
    assert approx(estimated_harvest, actual_harvest, 1e-3)

    platform_fees = actual_harvest * vault.platformFee() // 10000
    caller_incentive = actual_harvest * vault.callIncentive() // 10000

    assert approx(cvxcrv_balance(bob), caller_incentive, 1e-5)
    assert approx(
        cvxcrv_balance(vault.platform()), platform_initial_balance + platform_fees, 1e-5
    )
    assert approx(
        vault.totalUnderlying(),
        initial_vault_balance + actual_harvest - platform_fees - caller_incentive,
        1e-5,
    )
    for account in accounts:
        assert approx(
            vault.balanceOfUnderlying(account) - initial_balances[account.address],
            (actual_harvest - platform_fees - caller_incentive) // len(accounts),
            1e-5,
        )
    chain.revert()
