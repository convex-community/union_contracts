from decimal import Decimal

import brownie
from brownie import interface

from ....utils import approx, eth_to_cvx, cvxcrv_to_crv, eth_to_crv, crv_to_cvxcrv
from ....utils.cvxfxs import get_crv_to_eth_amount
from ....utils.pirex import get_cvx_to_pxcvx
from ....utils.constants import (
    ADDRESS_ZERO,
    FXS,
    SUSHI_ROUTER,
    WETH,
    PXCVX_TOKEN,
    CRV_TOKEN,
    CURVE_CVXCRV_CRV_POOL,
    CVXCRV_TOKEN, UNION_CRV,
)


def test_deposit_from_eth(fn_isolation, alice, vault, zaps):

    initial_vault_balance = vault.balanceOf(alice)

    amount = 1e18

    with brownie.reverts():
        zaps.depositFromEth(0, ADDRESS_ZERO, {"value": amount, "from": alice})

    received_cvxcrv = crv_to_cvxcrv(eth_to_crv(amount))
    zaps.depositFromEth(0, alice, {"value": amount, "from": alice})
    assert vault.balanceOf(alice) > initial_vault_balance
    assert approx(
        vault.balanceOfUnderlying(alice), received_cvxcrv, 1e-6
    )

    before_withdraw_balance = interface.IERC20(CVXCRV_TOKEN).balanceOf(alice)
    vault.withdrawAll(alice, {"from": alice})
    assert interface.IERC20(CVXCRV_TOKEN).balanceOf(alice) > before_withdraw_balance


def test_deposit_from_crv(fn_isolation, alice, zaps, vault):

    interface.IERC20(CRV_TOKEN).transfer(
        alice.address, 2e22, {"from": CURVE_CVXCRV_CRV_POOL}
    )
    interface.IERC20(CRV_TOKEN).approve(zaps, 2**256 - 1, {"from": alice})

    initial_vault_balance = vault.balanceOf(alice)

    amount = 1e22

    with brownie.reverts():
        zaps.depositFromCrv(amount, 0, ADDRESS_ZERO, {"from": alice})

    received_cvxcrv = crv_to_cvxcrv(amount)
    zaps.depositFromCrv(amount, 0, alice, {"from": alice})
    assert vault.balanceOf(alice) > initial_vault_balance
    assert approx(
        vault.balanceOfUnderlying(alice), received_cvxcrv, 1e-6
    )

    before_withdraw_balance = interface.IERC20(CVXCRV_TOKEN).balanceOf(alice)
    vault.withdrawAll(alice, {"from": alice})
    assert interface.IERC20(CVXCRV_TOKEN).balanceOf(alice) > before_withdraw_balance


def test_deposit_from_ucrv(fn_isolation, alice, zaps, vault):
    amount = 2e22
    interface.IERC20(CVXCRV_TOKEN).transfer(
        alice.address, amount, {"from": CURVE_CVXCRV_CRV_POOL}
    )
    interface.IERC20(CVXCRV_TOKEN).approve(UNION_CRV, 2**256 - 1, {"from": alice})
    interface.IERC20(UNION_CRV).approve(zaps, 2**256 - 1, {"from": alice})
    interface.IUnionVault(UNION_CRV).deposit(alice, amount, {"from": alice})
    initial_vault_balance = vault.balanceOf(alice)

    ucrv_amount = interface.IERC20(UNION_CRV).balanceOf(alice)
    withdrawal_penalty = (interface.IUnionVault(UNION_CRV).withdrawalPenalty()) / 10000
    with brownie.reverts():
        zaps.depositFromUCrv(ucrv_amount, 0, ADDRESS_ZERO, {"from": alice})

    received_cvxcrv = amount * (1 - withdrawal_penalty)
    zaps.depositFromUCrv(ucrv_amount, 0, alice, {"from": alice})
    assert vault.balanceOf(alice) > initial_vault_balance
    assert approx(
        vault.balanceOfUnderlying(alice), received_cvxcrv, 1e-3
    )


def test_deposit_from_sushi(fn_isolation, alice, zaps, vault):

    interface.IERC20(FXS).transfer(alice.address, 2e21, {"from": FXS})
    interface.IERC20(FXS).approve(zaps, 2**256 - 1, {"from": alice})

    initial_vault_balance = vault.balanceOf(alice)

    amount = 1e21

    with brownie.reverts():
        zaps.depositViaUniV2EthPair(
            amount, 0, SUSHI_ROUTER, FXS, ADDRESS_ZERO, {"from": alice}
        )
    eth_amount = interface.IUniV2Router(SUSHI_ROUTER).getAmountsOut(
        amount, [FXS, WETH]
    )[-1]
    received_pxcvx = crv_to_cvxcrv(eth_to_crv(eth_amount))
    zaps.depositViaUniV2EthPair(
        amount, 0, SUSHI_ROUTER, FXS, alice, {"from": alice}
    )
    assert vault.balanceOf(alice) > initial_vault_balance
    assert approx(
        vault.balanceOfUnderlying(alice), received_pxcvx, 1e-6
    )
