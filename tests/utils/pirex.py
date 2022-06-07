from brownie import interface

from tests.utils.constants import CURVE_CVX_PCVX_POOL


def get_cvx_to_pxcvx(amount):
    swap_amount = interface.ICurveFactoryPool(CURVE_CVX_PCVX_POOL).get_dy(1, 0, amount)
    return swap_amount if swap_amount > amount else amount


def get_pcvx_to_cvx(amount):
    return (
        interface.ICurveFactoryPool(CURVE_CVX_PCVX_POOL).get_dy(0, 1, amount)
        if amount > 0
        else 0
    )
