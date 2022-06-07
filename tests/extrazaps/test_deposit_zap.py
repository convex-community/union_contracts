from brownie import interface, chain
import brownie
from tests.utils import CURVE_CRV_ETH_POOL, CURVE_CVXCRV_CRV_POOL, approx
from tests.utils.constants import (
    CRV_TOKEN,
    ADDRESS_ZERO,
    SPELL,
    WETH,
    SUSHI_ROUTER,
)


def test_deposit_from_eth(alice, owner, vault, zaps):
    chain.snapshot()
    amount = 1e18
    crv_amount = interface.ICurveV2Pool(CURVE_CRV_ETH_POOL).get_dy(0, 1, amount)
    cvxcrv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(
        0, 1, crv_amount
    )
    ucrv_amount = (cvxcrv_amount * vault.totalSupply()) / vault.totalUnderlying()

    with brownie.reverts():
        zaps.depositFromEth(cvxcrv_amount * 2, alice, {"from": alice, "value": amount})
    with brownie.reverts():
        zaps.depositFromEth(0, ADDRESS_ZERO, {"from": alice, "value": amount})

    zaps.depositFromEth(0, alice, {"from": alice, "value": amount})

    assert approx(
        vault.balanceOf(alice) * 1e-18,
        ucrv_amount * 1e-18,
        1,
    )
    chain.revert()


def test_deposit_from_crv(alice, owner, vault, zaps):
    chain.snapshot()
    amount = 1e18
    cvxcrv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(
        0, 1, amount
    )
    ucrv_amount = (cvxcrv_amount * vault.totalSupply()) / vault.totalUnderlying()

    interface.IERC20(CRV_TOKEN).transfer(
        alice.address, 2e22, {"from": CURVE_CVXCRV_CRV_POOL}
    )

    interface.IERC20(CRV_TOKEN).approve(zaps, 2**256 - 1, {"from": alice})

    with brownie.reverts():
        zaps.depositFromCrv(amount, cvxcrv_amount * 2, alice, {"from": alice})
    with brownie.reverts():
        zaps.depositFromCrv(amount, 0, ADDRESS_ZERO, {"from": alice})

    zaps.depositFromCrv(amount, 0, alice, {"from": alice})

    assert approx(
        vault.balanceOf(alice) * 1e-18,
        ucrv_amount * 1e-18,
        1,
    )
    chain.revert()


def test_deposit_from_spell(alice, owner, vault, zaps):
    chain.snapshot()
    amount = 1e18
    interface.IERC20(SPELL).transfer(alice.address, 2e22, {"from": SPELL})

    eth_amount = interface.IUniV2Router(SUSHI_ROUTER).getAmountsOut(
        amount, [SPELL, WETH]
    )[-1]
    crv_amount = interface.ICurveV2Pool(CURVE_CRV_ETH_POOL).get_dy(0, 1, eth_amount)
    cvxcrv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(
        0, 1, crv_amount
    )
    ucrv_amount = (cvxcrv_amount * vault.totalSupply()) / vault.totalUnderlying()

    interface.IERC20(SPELL).approve(zaps, 2**256 - 1, {"from": alice})
    with brownie.reverts():
        zaps.depositFromCrv(amount, cvxcrv_amount * 2, alice, {"from": alice})
    with brownie.reverts():
        zaps.depositFromCrv(amount, 0, ADDRESS_ZERO, {"from": alice})

    zaps.depositViaUniV2EthPair(amount, 0, SUSHI_ROUTER, SPELL, alice, {"from": alice})

    assert approx(
        vault.balanceOf(alice) * 1e-18,
        ucrv_amount * 1e-18,
        1,
    )
    chain.revert()
