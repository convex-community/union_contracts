import brownie
import pytest
from brownie import chain, interface

from ..utils import approx, eth_to_cvx, cvxcrv_to_crv
from ..utils.cvxfxs import get_crv_to_eth_amount
from ..utils.pirex import get_cvx_to_pxcvx
from ..utils.constants import (
    ADDRESS_ZERO,
    CVX,
    ALCX,
    SUSHI_ROUTER,
    WETH,
    PXCVX_TOKEN,
    CRV_TOKEN,
    CURVE_CVXCRV_CRV_POOL,
    CVXCRV_TOKEN, NULL_ADDRESS,
)


@pytest.mark.parametrize("lock", [False, True])
def test_deposit_from_cvx(fn_isolation, alice, cvx_zaps, cvx_vault, lock):

    initial_vault_balance = cvx_vault.balanceOf(alice)
    interface.IERC20(CVX).approve(cvx_zaps, 2**256 - 1, {"from": alice})

    amount = 1e22

    # with brownie.reverts():
    #    cvx_zaps.depositFromCvx(amount, amount * 2, alice, {"from": alice})
    with brownie.reverts():
        cvx_zaps.depositFromCvx(amount, 0, ADDRESS_ZERO, lock, {"from": alice})

    received_pxcvx = amount if lock else get_cvx_to_pxcvx(amount)
    cvx_zaps.depositFromCvx(amount, 0, alice, lock, {"from": alice})
    assert cvx_vault.balanceOf(alice) > initial_vault_balance
    assert approx(
        cvx_vault.convertToAssets(cvx_vault.balanceOf(alice)), received_pxcvx, 1e-6
    )

    before_redeem_balance = interface.IERC20(PXCVX_TOKEN).balanceOf(alice)
    cvx_vault.redeem(cvx_vault.balanceOf(alice), alice, alice, {"from": alice})
    assert interface.IERC20(PXCVX_TOKEN).balanceOf(alice) > before_redeem_balance


@pytest.mark.parametrize("lock", [False, True])
def test_deposit_from_eth(fn_isolation, alice, cvx_zaps, cvx_vault, lock):

    initial_vault_balance = cvx_vault.balanceOf(alice)

    amount = 1e18
    # with brownie.reverts():
    #    cvx_zaps.depositFromEth(amount * 1e10, alice, {"value": amount, "from": alice})
    with brownie.reverts():
        cvx_zaps.depositFromEth(0, ADDRESS_ZERO, lock, {"value": amount, "from": alice})

    received_cvx = eth_to_cvx(amount)
    received_pxcvx = received_cvx if lock else get_cvx_to_pxcvx(received_cvx)
    cvx_zaps.depositFromEth(0, alice, lock, {"value": amount, "from": alice})
    assert cvx_vault.balanceOf(alice) > initial_vault_balance
    assert approx(
        cvx_vault.convertToAssets(cvx_vault.balanceOf(alice)), received_pxcvx, 1e-6
    )

    before_redeem_balance = interface.IERC20(PXCVX_TOKEN).balanceOf(alice)
    cvx_vault.redeem(cvx_vault.balanceOf(alice), alice, alice, {"from": alice})
    assert interface.IERC20(PXCVX_TOKEN).balanceOf(alice) > before_redeem_balance


@pytest.mark.parametrize("lock", [False, True])
def test_deposit_from_crv(fn_isolation, alice, cvx_zaps, cvx_vault, lock):

    interface.IERC20(CRV_TOKEN).transfer(
        alice.address, 2e22, {"from": CURVE_CVXCRV_CRV_POOL}
    )
    interface.IERC20(CRV_TOKEN).approve(cvx_zaps, 2**256 - 1, {"from": alice})

    initial_vault_balance = cvx_vault.balanceOf(alice)

    amount = 1e22

    # with brownie.reverts():
    #     cvx_zaps.depositFromCrv(
    #         amount, amount * 1e10, alice, {"from": alice}
    #     )
    with brownie.reverts():
        cvx_zaps.depositFromCrv(amount, 0, ADDRESS_ZERO, lock, {"from": alice})

    received_cvx = eth_to_cvx(get_crv_to_eth_amount(amount))
    received_pxcvx = received_cvx if lock else get_cvx_to_pxcvx(received_cvx)
    cvx_zaps.depositFromCrv(amount, 0, alice, lock, {"from": alice})
    assert cvx_vault.balanceOf(alice) > initial_vault_balance
    assert approx(
        cvx_vault.convertToAssets(cvx_vault.balanceOf(alice)), received_pxcvx, 1e-6
    )

    before_redeem_balance = interface.IERC20(PXCVX_TOKEN).balanceOf(alice)
    cvx_vault.redeem(cvx_vault.balanceOf(alice), alice, alice, {"from": alice})
    assert interface.IERC20(PXCVX_TOKEN).balanceOf(alice) > before_redeem_balance


@pytest.mark.parametrize("lock", [False, True])
def test_deposit_from_cvxcrv(fn_isolation, alice, cvx_zaps, cvx_vault, lock):

    interface.IERC20(CVXCRV_TOKEN).transfer(
        alice.address, 2e22, {"from": CURVE_CVXCRV_CRV_POOL}
    )
    interface.IERC20(CVXCRV_TOKEN).approve(cvx_zaps, 2**256 - 1, {"from": alice})

    initial_vault_balance = cvx_vault.balanceOf(alice)

    amount = 1e22

    # with brownie.reverts():
    #     cvx_zaps.depositFromCvxCrv(
    #         amount, amount * 1e10, alice, {"from": alice}
    #     )
    with brownie.reverts():
        cvx_zaps.depositFromCvxCrv(amount, 0, ADDRESS_ZERO, lock, {"from": alice})

    received_cvx = eth_to_cvx(get_crv_to_eth_amount(cvxcrv_to_crv(amount)))
    received_pxcvx = received_cvx if lock else get_cvx_to_pxcvx(received_cvx)
    cvx_zaps.depositFromCvxCrv(amount, 0, alice, lock, {"from": alice})
    assert cvx_vault.balanceOf(alice) > initial_vault_balance
    assert approx(
        cvx_vault.convertToAssets(cvx_vault.balanceOf(alice)), received_pxcvx, 1e-6
    )

    before_redeem_balance = interface.IERC20(PXCVX_TOKEN).balanceOf(alice)
    cvx_vault.redeem(cvx_vault.balanceOf(alice), alice, alice, {"from": alice})
    assert interface.IERC20(PXCVX_TOKEN).balanceOf(alice) > before_redeem_balance


@pytest.mark.parametrize("lock", [False, True])
def test_deposit_from_sushi(fn_isolation, alice, cvx_zaps, cvx_vault, lock):

    amount = 1e20

    interface.IERC20(ALCX).transfer(alice.address, amount, {"from": NULL_ADDRESS})
    interface.IERC20(ALCX).approve(cvx_zaps, 2 ** 256 - 1, {"from": alice})

    initial_vault_balance = cvx_vault.balanceOf(alice)

    with brownie.reverts("Invalid address!"):
        cvx_zaps.depositViaUniV2EthPair(
            amount, 0, SUSHI_ROUTER, ALCX, ADDRESS_ZERO, lock, {"from": alice}
        )
    # with brownie.reverts():
    #     cvx_zaps.depositViaUniV2EthPair(
    #         amount, 1e50, SUSHI_ROUTER, FXS, alice, {"from": alice}
    #     )
    eth_amount = interface.IUniV2Router(SUSHI_ROUTER).getAmountsOut(
        amount, [ALCX, WETH]
    )[-1]
    # in case there is already eth in the contract (happened during testing)
    eth_amount = eth_amount + cvx_zaps.balance()
    received_cvx = eth_to_cvx(eth_amount)
    received_pxcvx = received_cvx if lock else get_cvx_to_pxcvx(received_cvx)
    tx = cvx_zaps.depositViaUniV2EthPair(
        amount, 0, SUSHI_ROUTER, ALCX, alice, lock, {"from": alice}
    )
    assert cvx_vault.balanceOf(alice) > initial_vault_balance
    assert approx(
        cvx_vault.convertToAssets(cvx_vault.balanceOf(alice) - initial_vault_balance), received_pxcvx, 1e-6
    )

    before_redeem_balance = interface.IERC20(PXCVX_TOKEN).balanceOf(alice)
    cvx_vault.redeem(cvx_vault.balanceOf(alice), alice, alice, {"from": alice})
    assert interface.IERC20(PXCVX_TOKEN).balanceOf(alice) > before_redeem_balance
