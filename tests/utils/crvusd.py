from brownie import interface

from .constants import (
    CVX,
    CURVE_CVXPRISMA_PRISMA_POOL,
    CURVE_PRISMA_MKUSD_POOL,
    MKUSD_TOKEN,
    PRISMA, CURVE_TRICRV_POOL, SCRVUSD_VAULT,
)
from .cvxfxs import get_cvx_to_eth_amount


def eth_to_crvusd(amount):
    return (
        interface.ICurveV2Pool(CURVE_TRICRV_POOL).get_dy(1, 0, amount)
        if amount > 0
        else 0
    )


def crvusd_to_eth(amount):
    return (
        interface.ICurveV2Pool(CURVE_TRICRV_POOL).get_dy(0, 1, amount)
        if amount > 0
        else 0
    )


def crvusd_to_scrvusd(amount):
    if amount == 0:
        return 0
    return interface.IERC4626(SCRVUSD_VAULT).convertToShares(amount)


def scrvusd_to_crvusd(amount):
    if amount == 0:
        return 0
    return interface.IERC4626(SCRVUSD_VAULT).convertToAssets(amount)