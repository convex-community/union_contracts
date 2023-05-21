from brownie import interface

from ..utils import approx, eth_to_crv, crv_to_cvxcrv
from ..utils.constants import (
    CVX,
    CRV,
    CVXCRV_TOKEN,
    TRICRYPTO,
    USDT_TOKEN,
    FXS,
    SUSHI_ROUTER,
    WETH,
)
from ..utils.cvxfxs import get_cvx_to_eth_amount
from ..utils.pirex import get_pcvx_to_cvx_via_lpxcvx


def test_withdraw_as_cvx(fn_isolation, alice, cvx_zaps, cvx_vault):

    initial_vault_balance = cvx_vault.balanceOf(alice)
    interface.IERC20(CVX).approve(cvx_zaps, 2**256 - 1, {"from": alice})

    amount = 1e21

    cvx_zaps.depositFromCvx(amount, 1, alice, False, {"from": alice})
    assert cvx_vault.balanceOf(alice) > initial_vault_balance

    pcvx_received = cvx_vault.previewRedeem(cvx_vault.balanceOf(alice))
    cvx_received = get_pcvx_to_cvx_via_lpxcvx(pcvx_received)

    before_redeem_balance = interface.IERC20(CVX).balanceOf(alice)
    interface.IERC20(cvx_vault).approve(cvx_zaps, 2**256 - 1, {"from": alice})
    cvx_zaps.claimFromVaultAsCvx(cvx_vault.balanceOf(alice), 1, alice, {"from": alice})
    assert cvx_vault.balanceOf(alice) == 0
    assert cvx_vault.balanceOf(cvx_zaps) == 0
    assert approx(
        interface.IERC20(CVX).balanceOf(alice),
        before_redeem_balance + cvx_received,
        1e-3,
    )


def test_withdraw_as_eth(fn_isolation, alice, cvx_zaps, cvx_vault):

    initial_vault_balance = cvx_vault.balanceOf(alice)
    interface.IERC20(CVX).approve(cvx_zaps, 2**256 - 1, {"from": alice})

    amount = 1e21

    cvx_zaps.depositFromCvx(amount, 1, alice, False, {"from": alice})
    assert cvx_vault.balanceOf(alice) > initial_vault_balance

    pcvx_received = cvx_vault.previewRedeem(cvx_vault.balanceOf(alice))
    token_received = get_cvx_to_eth_amount(get_pcvx_to_cvx_via_lpxcvx(pcvx_received))

    before_redeem_balance = alice.balance()
    interface.IERC20(cvx_vault).approve(cvx_zaps, 2**256 - 1, {"from": alice})

    cvx_zaps.claimFromVaultAsEth(cvx_vault.balanceOf(alice), 1, alice, {"from": alice})

    assert cvx_vault.balanceOf(alice) == 0
    assert cvx_vault.balanceOf(cvx_zaps) == 0
    assert approx(alice.balance(), before_redeem_balance + token_received, 1e-3)


def test_withdraw_as_crv(fn_isolation, alice, cvx_zaps, cvx_vault):

    initial_vault_balance = cvx_vault.balanceOf(alice)
    interface.IERC20(CVX).approve(cvx_zaps, 2**256 - 1, {"from": alice})

    amount = 1e21

    cvx_zaps.depositFromCvx(amount, 1, alice, False, {"from": alice})
    assert cvx_vault.balanceOf(alice) > initial_vault_balance

    pcvx_received = cvx_vault.previewRedeem(cvx_vault.balanceOf(alice))
    token_received = eth_to_crv(
        get_cvx_to_eth_amount(get_pcvx_to_cvx_via_lpxcvx(pcvx_received))
    )

    before_redeem_balance = interface.IERC20(CRV).balanceOf(alice)
    interface.IERC20(cvx_vault).approve(cvx_zaps, 2**256 - 1, {"from": alice})

    cvx_zaps.claimFromVaultAsCrv(cvx_vault.balanceOf(alice), 1, alice, {"from": alice})
    assert cvx_vault.balanceOf(alice) == 0
    assert cvx_vault.balanceOf(cvx_zaps) == 0
    assert approx(
        interface.IERC20(CRV).balanceOf(alice),
        before_redeem_balance + token_received,
        1e-3,
    )


def test_withdraw_as_cvxcrv(fn_isolation, alice, cvx_zaps, cvx_vault):

    initial_vault_balance = cvx_vault.balanceOf(alice)
    interface.IERC20(CVX).approve(cvx_zaps, 2**256 - 1, {"from": alice})

    amount = 1e21

    cvx_zaps.depositFromCvx(amount, 1, alice, False, {"from": alice})
    assert cvx_vault.balanceOf(alice) > initial_vault_balance

    pcvx_received = cvx_vault.previewRedeem(cvx_vault.balanceOf(alice))
    token_received = crv_to_cvxcrv(
        eth_to_crv(get_cvx_to_eth_amount(get_pcvx_to_cvx_via_lpxcvx(pcvx_received)))
    )

    before_redeem_balance = interface.IERC20(CVXCRV_TOKEN).balanceOf(alice)
    interface.IERC20(cvx_vault).approve(cvx_zaps, 2**256 - 1, {"from": alice})

    cvx_zaps.claimFromVaultAsCvxCrv(
        cvx_vault.balanceOf(alice), 1, alice, {"from": alice}
    )
    assert cvx_vault.balanceOf(alice) == 0
    assert cvx_vault.balanceOf(cvx_zaps) == 0
    assert approx(
        interface.IERC20(CVXCRV_TOKEN).balanceOf(alice),
        before_redeem_balance + token_received,
        1e-3,
    )


def test_withdraw_as_usdt(fn_isolation, alice, cvx_zaps, cvx_vault):

    initial_vault_balance = cvx_vault.balanceOf(alice)
    interface.IERC20(CVX).approve(cvx_zaps, 2**256 - 1, {"from": alice})

    amount = 1e21

    cvx_zaps.depositFromCvx(amount, 1, alice, False, {"from": alice})
    assert cvx_vault.balanceOf(alice) > initial_vault_balance

    pcvx_received = cvx_vault.previewRedeem(cvx_vault.balanceOf(alice))
    eth_amount = get_cvx_to_eth_amount(get_pcvx_to_cvx_via_lpxcvx(pcvx_received))
    usdt_amount = interface.ICurveV2Pool(TRICRYPTO).get_dy(2, 0, eth_amount)

    before_redeem_balance = interface.IERC20(USDT_TOKEN).balanceOf(alice)
    interface.IERC20(cvx_vault).approve(cvx_zaps, 2**256 - 1, {"from": alice})

    cvx_zaps.claimFromVaultAsUsdt(cvx_vault.balanceOf(alice), 1, alice, {"from": alice})
    assert cvx_vault.balanceOf(alice) == 0
    assert cvx_vault.balanceOf(cvx_zaps) == 0
    assert approx(
        interface.IERC20(USDT_TOKEN).balanceOf(alice),
        before_redeem_balance + usdt_amount,
        1e-3,
    )


def test_withdraw_via_sushi(fn_isolation, alice, cvx_zaps, cvx_vault):

    initial_vault_balance = cvx_vault.balanceOf(alice)
    interface.IERC20(CVX).approve(cvx_zaps, 2**256 - 1, {"from": alice})

    amount = 1e21

    cvx_zaps.depositFromCvx(amount, 1, alice, False, {"from": alice})
    assert cvx_vault.balanceOf(alice) > initial_vault_balance

    pcvx_received = cvx_vault.previewRedeem(cvx_vault.balanceOf(alice))
    eth_amount = get_cvx_to_eth_amount(get_pcvx_to_cvx_via_lpxcvx(pcvx_received))
    spell_amount = interface.IUniV2Router(SUSHI_ROUTER).getAmountsOut(
        eth_amount, [WETH, FXS]
    )[-1]

    before_redeem_balance = interface.IERC20(FXS).balanceOf(alice)
    interface.IERC20(cvx_vault).approve(cvx_zaps, 2**256 - 1, {"from": alice})

    cvx_zaps.claimFromVaultViaUniV2EthPair(
        cvx_vault.balanceOf(alice), 1, SUSHI_ROUTER, FXS, alice, {"from": alice}
    )
    assert cvx_vault.balanceOf(alice) == 0
    assert cvx_vault.balanceOf(cvx_zaps) == 0
    assert approx(
        interface.IERC20(FXS).balanceOf(alice),
        before_redeem_balance + spell_amount,
        1e-3,
    )
