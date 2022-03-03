from brownie import interface, chain

from ....utils.constants import CVXFXS_STAKING_CONTRACT
from ....utils import approx, cvxfxs_lp_balance, fxs_balance
from ....utils.cvxfxs import calc_harvest_amount_curve, estimate_lp_tokens_received


def test_harvest_single_staker(alice, bob, owner, vault, strategy):
    chain.snapshot()
    alice_initial_balance = cvxfxs_lp_balance(alice)
    bob_initial_balance = fxs_balance(bob)
    platform_initial_balance = fxs_balance(vault.platform())
    vault.depositAll(alice, {"from": alice})
    chain.sleep(100000)
    chain.mine(1)
    estimated_harvested_fxs = calc_harvest_amount_curve(strategy, True)

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
