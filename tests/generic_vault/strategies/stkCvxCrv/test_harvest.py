import brownie
import pytest
from brownie import interface, chain


from ....utils.constants import (
    CRV,
    CURVE_CVXCRV_CRV_POOL,
    CURVE_VOTING_ESCROW, CVX, CURVE_CVX_ETH_POOL, CVX_STAKING_CONTRACT, USDT_TOKEN, TRICRYPTO,
    UNISWAP_ETH_USDT_POOL, CURVE_CRV_ETH_POOL,
)
from ....utils import approx, calc_staked_cvxcrv_harvest, cvxcrv_balance, calc_harvest_amount_in_cvxcrv


@pytest.mark.parametrize("weight", [0, 5000, 10000])
def test_harvest_single_staker(fn_isolation, alice, bob, owner, vault, strategy, wrapper, weight):
    vault.setRewardWeight(weight, {'from': owner})
    alice_initial_balance = cvxcrv_balance(alice)
    bob_initial_balance = cvxcrv_balance(bob)
    platform_initial_balance = cvxcrv_balance(vault.platform())
    vault.depositAll(alice, {"from": alice})
    chain.sleep(100000)
    chain.mine(1)
    estimated_harvest = calc_staked_cvxcrv_harvest(strategy, wrapper)
    tx = vault.harvest({"from": bob})

    actual_harvest = tx.events["Harvest"]["_value"]

    platform_fees = estimated_harvest * vault.platformFee() // 10000
    caller_incentive = estimated_harvest * vault.callIncentive() // 10000

    assert approx(estimated_harvest, platform_fees + caller_incentive + actual_harvest, 1e-3)
    assert approx(cvxcrv_balance(bob), bob_initial_balance + caller_incentive, 1e-3)
    assert approx(
        cvxcrv_balance(vault.platform()), platform_initial_balance + platform_fees, 1e-3
    )
    assert approx(
        interface.ICvxCrvStaking(wrapper).balanceOf(strategy),
        alice_initial_balance + actual_harvest,
        1e-3,
    )


def test_harvest_force_lock(fn_isolation, alice, bob, owner, vault, strategy, wrapper):
    alice_initial_balance = cvxcrv_balance(alice)
    bob_initial_balance = cvxcrv_balance(bob)
    platform_initial_balance = cvxcrv_balance(vault.platform())
    vault.depositAll(alice, {"from": alice})
    chain.sleep(100000)
    chain.mine(1)
    estimated_harvest = calc_staked_cvxcrv_harvest(strategy, wrapper, True)
    estimated_harvest_no_lock = calc_staked_cvxcrv_harvest(strategy, wrapper)
    assert estimated_harvest != estimated_harvest_no_lock
    tx = vault.harvest(0, True, {"from": bob})

    actual_harvest = tx.events["Harvest"]["_value"]

    platform_fees = estimated_harvest * vault.platformFee() // 10000
    caller_incentive = estimated_harvest * vault.callIncentive() // 10000

    assert approx(estimated_harvest, platform_fees + caller_incentive + actual_harvest, 1e-3)
    assert approx(cvxcrv_balance(bob), bob_initial_balance + caller_incentive, 1e-3)
    assert approx(
        cvxcrv_balance(vault.platform()), platform_initial_balance + platform_fees, 1e-3
    )
    assert approx(
        interface.ICvxCrvStaking(wrapper).balanceOf(strategy),
        alice_initial_balance + actual_harvest,
        1e-3,
    )


def test_harvest_cvx_oracle_failure(fn_isolation, alice, bob, owner, vault, strategy, wrapper):

    cvx = interface.IERC20(CVX)
    cvx.approve(CURVE_CVX_ETH_POOL, 2**256 - 1, {"from": CVX_STAKING_CONTRACT})
    interface.ICurveV2Pool(CURVE_CVX_ETH_POOL).exchange(
        1,
        0,
        cvx.balanceOf(CVX_STAKING_CONTRACT),
        0,
        False,
        {"from": CVX_STAKING_CONTRACT},
    )

    vault.depositAll(alice, {"from": alice})
    chain.sleep(100000)
    chain.mine(1)
    with brownie.reverts():
        tx = vault.harvest({"from": alice})


def test_harvest_crv_oracle_failure(fn_isolation, alice, bob, owner, vault, strategy, wrapper):
    vault.setRewardWeight(10000, {'from': owner})
    interface.ICurveV2Pool(CURVE_CRV_ETH_POOL).exchange_underlying(
        0,
        1,
        interface.ICurveV2Pool(CURVE_CVX_ETH_POOL).balance(),
        0,
        {"from": CURVE_CVX_ETH_POOL,
         "value": interface.ICurveV2Pool(CURVE_CVX_ETH_POOL).balance()
         },
    )

    vault.depositAll(alice, {"from": alice})
    chain.sleep(100000)
    chain.mine(1)
    with brownie.reverts():
        tx = vault.harvest({"from": alice})


def test_harvest_tricrypto_oracle_failure(fn_isolation, alice, bob, owner, vault, strategy, wrapper):
    vault.setRewardWeight(10000, {'from': owner})

    vault.depositAll(alice, {"from": alice})
    chain.sleep(100000)
    chain.mine(1)

    usdt = interface.IERC20(USDT_TOKEN)
    usdt.approve(TRICRYPTO, 2**256 - 1, {"from": UNISWAP_ETH_USDT_POOL})
    interface.ICurveV2Pool(TRICRYPTO).exchange(
        0,
        2,
        usdt.balanceOf(UNISWAP_ETH_USDT_POOL),
        0,
        False,
        {"from": UNISWAP_ETH_USDT_POOL},
    )
    with brownie.reverts("Slippage"):
        tx = vault.harvest({"from": alice})


def test_harvest_min_amount_out(fn_isolation, alice, owner, vault, strategy, wrapper):
    vault.setRewardWeight(10000, {'from': owner})
    vault.depositAll(alice, {"from": alice})
    chain.sleep(100000)
    chain.mine(1)
    with brownie.reverts("slippage"):
        tx = vault.harvest(1e26, {"from": alice})


def test_harvest_no_discount(fn_isolation, alice, bob, owner, vault, strategy, wrapper):
    crv = interface.IERC20(CRV)
    vault.setRewardWeight(10000, {'from': owner})
    crv.approve(CURVE_CVXCRV_CRV_POOL, 2**256 - 1, {"from": CURVE_VOTING_ESCROW})
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
    vault.depositAll(alice, {"from": alice})
    chain.sleep(100000)
    chain.mine(1)
    estimated_harvest = calc_staked_cvxcrv_harvest(strategy, wrapper)
    tx = vault.harvest({"from": bob})

    actual_harvest = tx.events["Harvest"]["_value"]

    platform_fees = estimated_harvest * vault.platformFee() // 10000
    caller_incentive = estimated_harvest * vault.callIncentive() // 10000

    assert approx(estimated_harvest, platform_fees + caller_incentive + actual_harvest, 1e-3)
    assert approx(cvxcrv_balance(bob), bob_initial_balance + caller_incentive, 1e-3)
    assert approx(
        cvxcrv_balance(vault.platform()), platform_initial_balance + platform_fees, 1e-3
    )
    assert approx(
        interface.ICvxCrvStaking(wrapper).balanceOf(strategy),
        alice_initial_balance + actual_harvest,
        1e-3,
    )


def test_harvest_multiple_stakers(fn_isolation, alice, bob, charlie, dave, owner, vault, strategy, wrapper):

    vault.setRewardWeight(5000, {'from': owner})
    initial_balances = {}
    accounts = [alice, bob, charlie, dave]

    for account in accounts:
        initial_balances[account.address] = cvxcrv_balance(account)
        vault.depositAll(account, {"from": account})

    platform_initial_balance = cvxcrv_balance(vault.platform())

    chain.sleep(100000)
    chain.mine(1)

    estimated_harvest = calc_staked_cvxcrv_harvest(strategy, wrapper)
    tx = vault.harvest({"from": bob})

    actual_harvest = tx.events["Harvest"]["_value"]

    platform_fees = estimated_harvest * vault.platformFee() // 10000
    caller_incentive = estimated_harvest * vault.callIncentive() // 10000

    assert approx(estimated_harvest, platform_fees + caller_incentive + actual_harvest, 1e-3)
    assert approx(cvxcrv_balance(bob), caller_incentive, 1e-3)
    assert approx(
        cvxcrv_balance(vault.platform()), platform_initial_balance + platform_fees, 1e-3
    )
    for account in accounts:
        underlying_balance = vault.balanceOf(account) * interface.ICvxCrvStaking(wrapper).balanceOf(strategy) / vault.totalSupply()
        assert approx(
            underlying_balance - initial_balances[account.address],
            (actual_harvest) // len(accounts),
            1e-3,
        )
