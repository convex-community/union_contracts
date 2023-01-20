import brownie
import pytest
from brownie import interface
from decimal import Decimal

from ....utils import get_crv_to_eth_amount, approx, eth_to_cvx
from ....utils.aurabal import (
    estimate_underlying_received_baleth,
    get_aurabal_to_lptoken_amount,
)
from ....utils.constants import (
    SUSHI_ROUTER,
    WETH,
    SPELL,
    ADDRESS_ZERO,
    BAL_TOKEN, CURVE_CVXCRV_CRV_POOL, CRV, CVX, TRICRYPTO, USDT_TOKEN, FXS, CONVEX_LOCKER, TRIPOOL,
    CONVEX_TRIPOOL_REWARDS,
)


def test_claim_as_eth(fn_isolation, alice, bob, vault, strategy, zaps):
    amount = int(1e21)
    alice_original_eth_balance = alice.balance()
    vault.deposit(alice, amount, {"from": alice})
    vault.deposit(bob, amount, {"from": bob})

    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000
    crv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(
        1, 0, amount * (1 - withdrawal_penalty)
    )
    eth_amount = get_crv_to_eth_amount(crv_amount)

    vault.approve(zaps, 2**256 - 1, {"from": alice})

    tx = zaps.claimFromVaultAsEth(
        vault.balanceOf(alice), 0, alice.address, {"from": alice}
    )
    assert approx(alice.balance(), eth_amount + alice_original_eth_balance, 1e-3)


def test_claim_as_crv(fn_isolation, alice, bob, vault, strategy, zaps):
    amount = int(1e21)
    alice_original_balance = interface.IERC20(CRV).balanceOf(alice)
    vault.deposit(alice, amount, {"from": alice})
    vault.deposit(bob, amount, {"from": bob})

    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000
    crv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(
        1, 0, amount * (1 - withdrawal_penalty)
    )

    vault.approve(zaps, 2**256 - 1, {"from": alice})

    tx = zaps.claimFromVaultAsCrv(
        vault.balanceOf(alice), 0, alice.address, {"from": alice}
    )
    assert approx(interface.IERC20(CRV).balanceOf(alice), crv_amount + alice_original_balance, 1e-3)


def test_claim_as_cvx(fn_isolation, alice, bob, vault, strategy, zaps):
    amount = int(1e21)
    alice_original_balance = interface.IERC20(CVX).balanceOf(alice)
    vault.deposit(alice, amount, {"from": alice})
    vault.deposit(bob, amount, {"from": bob})

    withdrawal_penalty = (vault.withdrawalPenalty()) / 10000
    crv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(
        1, 0, amount * (1 - withdrawal_penalty)
    )
    cvx_amount = eth_to_cvx(get_crv_to_eth_amount(crv_amount))

    vault.approve(zaps, 2**256 - 1, {"from": alice})

    tx = zaps.claimFromVaultAsCvx(
        vault.balanceOf(alice), 0, alice.address, False, {"from": alice}
    )
    assert approx(interface.IERC20(CVX).balanceOf(alice), cvx_amount + alice_original_balance, 1e-3)


def test_claim_as_cvx_and_lock(fn_isolation, alice, bob, vault, strategy, zaps):
    amount = int(1e21)
    alice_original_balance = interface.IERC20(CVX).balanceOf(alice)
    vault.deposit(alice, amount, {"from": alice})
    vault.deposit(bob, amount, {"from": bob})

    withdrawal_penalty = (vault.withdrawalPenalty()) / 10000
    crv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(
        1, 0, amount * (1 - withdrawal_penalty)
    )
    cvx_amount = eth_to_cvx(get_crv_to_eth_amount(crv_amount))

    vault.approve(zaps, 2**256 - 1, {"from": alice})

    tx = zaps.claimFromVaultAsCvx(
        vault.balanceOf(alice), 0, alice.address, True, {"from": alice}
    )
    assert approx(interface.ICVXLocker(CONVEX_LOCKER).balances(alice)[0], cvx_amount + alice_original_balance, 1e-3)


def test_claim_as_usdt(fn_isolation, alice, bob, vault, strategy, zaps):
    amount = int(1e21)
    alice_original_balance = interface.IERC20(USDT_TOKEN).balanceOf(alice)
    vault.deposit(alice, amount, {"from": alice})
    vault.deposit(bob, amount, {"from": bob})

    withdrawal_penalty = (vault.withdrawalPenalty()) / 10000
    crv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(
        1, 0, amount * (1 - withdrawal_penalty)
    )
    eth_amount = get_crv_to_eth_amount(crv_amount)
    usdt_amount = interface.ICurveV2Pool(TRICRYPTO).get_dy(2, 0, eth_amount)

    vault.approve(zaps, 2**256 - 1, {"from": alice})

    tx = zaps.claimFromVaultAsUsdt(
        vault.balanceOf(alice), 0, alice.address, {"from": alice}
    )
    assert approx(interface.IERC20(USDT_TOKEN).balanceOf(alice), usdt_amount + alice_original_balance, 1e-3)


def test_claim_as_tripool(fn_isolation, alice, bob, vault, strategy, zaps):
    amount = int(1e21)
    vault.deposit(alice, amount, {"from": alice})
    vault.deposit(bob, amount, {"from": bob})

    withdrawal_penalty = (vault.withdrawalPenalty()) / 10000
    crv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(
        1, 0, amount * (1 - withdrawal_penalty)
    )
    eth_amount = get_crv_to_eth_amount(crv_amount)
    usdt_amount = interface.ICurveV2Pool(TRICRYPTO).get_dy(2, 0, eth_amount)
    tricrv_amount = (
        usdt_amount * 1e12 / interface.ITriPool(TRIPOOL).get_virtual_price()
    )

    vault.approve(zaps, 2**256 - 1, {"from": alice})

    tx = zaps.claimFromVaultAndStakeIn3PoolConvex(
        vault.balanceOf(alice), 0, alice.address, {"from": alice}
    )
    assert approx(interface.IRewards(CONVEX_TRIPOOL_REWARDS).balanceOf(alice) * 1e-18, tricrv_amount, 1e-3)


def test_claim_as_fxs(
    fn_isolation, alice, bob, vault, strategy, zaps
):
    amount = int(1e21)
    for i, account in enumerate([alice, bob]):
        vault.deposit(account, amount, {"from": account})

    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000
    crv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(
        1, 0, amount * (1 - withdrawal_penalty)
    )
    eth_amount = get_crv_to_eth_amount(crv_amount)

    spell_amount = interface.IUniV2Router(SUSHI_ROUTER).getAmountsOut(
        eth_amount, [WETH, FXS]
    )[-1]
    vault.approve(zaps, 2**256 - 1, {"from": alice})

    zaps.claimFromVaultViaUniV2EthPair(
        amount, 0, SUSHI_ROUTER, FXS, alice.address, {"from": alice}
    )
    assert interface.IERC20(FXS).balanceOf(alice) == spell_amount


def test_not_to_zero(alice, vault, strategy, zaps):

    with brownie.reverts("Invalid address!"):
        zaps.claimFromVaultViaUniV2EthPair(
            int(1e18), 0, SUSHI_ROUTER, SPELL, ADDRESS_ZERO, {"from": alice}
        )

    with brownie.reverts("Invalid address!"):
        zaps.claimFromVaultAsEth(
            vault.balanceOf(alice), 0, ADDRESS_ZERO, {"from": alice}
        )
