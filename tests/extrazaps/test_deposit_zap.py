from brownie import interface, chain
import brownie
from tests.utils import CURVE_CRV_ETH_POOL, CURVE_CVXCRV_CRV_POOL, approx
from tests.utils.constants import CVXCRV_REWARDS


def test_deposit_zap(alice, owner, vault, zaps):
    chain.snapshot()
    amount = 1e18
    crv_amount = interface.ICurveV2Pool(CURVE_CRV_ETH_POOL).get_dy(0, 1, amount)
    cvxcrv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(
        0, 1, crv_amount
    )

    with brownie.reverts():
        zaps.depositFromEth(cvxcrv_amount * 2, alice, {"from": alice, "value": amount})
    zaps.depositFromEth(0, alice, {"from": alice, "value": amount})

    assert approx(
        interface.IBasicRewards(CVXCRV_REWARDS).balanceOf(alice) * 1e-18,
        cvxcrv_amount * 1e-18,
        1,
    )
