from brownie import interface

from .constants import (
    CVX, CURVE_PRISMA_ETH_POOL, CURVE_CVXPRISMA_PRISMA_POOL, CURVE_PRISMA_MKUSD_POOL, MKUSD_TOKEN, PRISMA,
)
from .cvxfxs import get_cvx_to_eth_amount


def eth_to_prisma(amount):
    return (
        interface.ICurveV2Pool(CURVE_PRISMA_ETH_POOL).get_dy(0, 1, amount)
        if amount > 0
        else 0
    )


def prisma_to_eth(amount):
    return (
        interface.ICurveV2Pool(CURVE_PRISMA_ETH_POOL).get_dy(1, 0, amount)
        if amount > 0
        else 0
    )


def prisma_to_cvxprisma(amount):
    if amount == 0:
        return 0
    return interface.ICurvePool(CURVE_CVXPRISMA_PRISMA_POOL).get_dy(0, 1, amount)


def cvxprisma_to_prisma(amount):
    if amount == 0:
        return 0
    return interface.ICurvePool(CURVE_CVXPRISMA_PRISMA_POOL).get_dy(1, 0, amount)


def prisma_to_mkusd(amount):
    if amount == 0:
        return 0
    return interface.ICurveV2Pool(CURVE_PRISMA_MKUSD_POOL).get_dy(1, 0, amount)


def mkusd_to_prisma(amount):
    print("MKUSD Amount,", amount)
    if amount == 0:
        return 0
    return interface.ICurveV2Pool(CURVE_PRISMA_MKUSD_POOL).get_dy(0, 1, amount)


def calc_staking_harvest_amount(strategy, staking, lock=False):

    prisma_balance, eth_balance = calc_staking_rewards(strategy, staking)
    if eth_balance > 0:
        prisma_balance += eth_to_prisma(eth_balance)
    return prisma_balance if lock else prisma_to_cvxprisma(prisma_balance)


def calc_staking_rewards(strategy, staking):
    staking_rewards = staking.claimableRewards(strategy)
    eth_balance = 0
    prisma_rewards = 0
    for rewards in staking_rewards:
        token, amount = rewards
        if token == MKUSD_TOKEN:
            prisma_rewards += mkusd_to_prisma(amount)
        elif token == CVX:
            eth_balance += get_cvx_to_eth_amount(amount)
        elif token == PRISMA:
            prisma_rewards += amount

    return prisma_rewards, eth_balance

