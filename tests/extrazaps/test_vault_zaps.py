import brownie
import pytest
from brownie import interface, chain
from decimal import Decimal

from ..utils.constants import (
    CVXCRV,
    CONVEX_TRIPOOL_REWARDS,
    TRICRYPTO,
    CURVE_CVXCRV_CRV_POOL,
    CVXCRV_REWARDS,
    CURVE_CRV_ETH_POOL,
    CURVE_CVX_ETH_POOL,
    USDT_TOKEN,
    TRIPOOL,
    CONVEX_LOCKER,
)
from ..utils import cvxcrv_balance, approx


def test_claim_as_usdt(alice, bob, charlie, vault, zaps):
    amount = int(1e21)
    chain.snapshot()
    for i, account in enumerate([alice, bob, charlie]):
        vault.deposit(account, amount, {"from": account})

    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000
    crv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(
        1, 0, amount * (1 - withdrawal_penalty)
    )
    eth_amount = interface.ICurveV2Pool(CURVE_CRV_ETH_POOL).get_dy(1, 0, crv_amount)
    usdt_amount = interface.ICurveV2Pool(TRICRYPTO).get_dy(2, 0, eth_amount)
    vault.approve(zaps, 2 ** 256 - 1, {"from": alice})
    zaps.claimFromVaultAsUsdt(vault.balanceOf(alice), 0, alice.address, {"from": alice})
    assert interface.IERC20(USDT_TOKEN).balanceOf(alice) == usdt_amount
    chain.revert()


def test_claim_as_usdt_and_stake(alice, bob, charlie, vault, zaps):
    amount = int(1e21)
    chain.snapshot()
    for i, account in enumerate([alice, bob, charlie]):
        vault.deposit(account, amount, {"from": account})

    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000
    crv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(
        1, 0, amount * (1 - withdrawal_penalty)
    )
    eth_amount = interface.ICurveV2Pool(CURVE_CRV_ETH_POOL).get_dy(1, 0, crv_amount)
    usdt_amount = interface.ICurveV2Pool(TRICRYPTO).get_dy(2, 0, eth_amount)
    tricrv_amount = (
        usdt_amount * 1e12 // interface.ITriPool(TRIPOOL).get_virtual_price()
    )
    vault.approve(zaps, 2 ** 256 - 1, {"from": alice})
    zaps.claimFromVaultAndStakeIn3PoolConvex(
        vault.balanceOf(alice), 0, alice.address, {"from": alice}
    )
    assert approx(
        interface.IRewards(CONVEX_TRIPOOL_REWARDS).balanceOf(alice) * 1e-18,
        tricrv_amount,
        1,
    )
    chain.revert()


def test_claim_as_cvx_and_lock(alice, bob, charlie, vault, zaps):
    amount = int(1e21)
    chain.snapshot()
    for i, account in enumerate([alice, bob, charlie]):
        vault.deposit(account, amount, {"from": account})

    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000
    crv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(
        1, 0, amount * (1 - withdrawal_penalty)
    )
    eth_amount = interface.ICurveV2Pool(CURVE_CRV_ETH_POOL).get_dy(1, 0, crv_amount)
    cvx_amount = interface.ICurveV2Pool(CURVE_CVX_ETH_POOL).get_dy(0, 1, eth_amount)
    vault.approve(zaps, 2 ** 256 - 1, {"from": alice})
    zaps.claimFromVaultAsCvxAndLock(
        vault.balanceOf(alice), 0, alice.address, {"from": alice}
    )
    assert interface.ICVXLocker(CONVEX_LOCKER).balances(alice)[0] == cvx_amount
    chain.revert()
