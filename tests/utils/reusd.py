from brownie import interface

from .constants import (
    REUSD_TOKEN,
    REUSD_POOL,
    SREUSD_VAULT,
)
from .crvusd import eth_to_crvusd, crvusd_to_eth, crvusd_to_scrvusd, scrvusd_to_crvusd


def scrvusd_to_reusd(amount):
    """Convert scrvUSD to reUSD via Curve pool (scrvUSD=1, reUSD=0)"""
    if amount == 0:
        return 0
    return interface.ICurveStableSwapNG(REUSD_POOL).get_dy(1, 0, amount)


def reusd_to_scrvusd(amount):
    """Convert reUSD to scrvUSD via Curve pool (reUSD=0, scrvUSD=1)"""
    if amount == 0:
        return 0
    return interface.ICurveStableSwapNG(REUSD_POOL).get_dy(0, 1, amount)


def eth_to_reusd(amount):
    """Convert ETH to reUSD via ETH -> crvUSD -> scrvUSD -> reUSD"""
    if amount == 0:
        return 0
    crvusd_amount = eth_to_crvusd(amount)
    scrvusd_amount = crvusd_to_scrvusd(crvusd_amount)
    return scrvusd_to_reusd(scrvusd_amount)


def reusd_to_eth(amount):
    """Convert reUSD to ETH via reUSD -> scrvUSD -> crvUSD -> ETH"""
    if amount == 0:
        return 0
    scrvusd_amount = reusd_to_scrvusd(amount)
    crvusd_amount = scrvusd_to_crvusd(scrvusd_amount)
    return crvusd_to_eth(crvusd_amount)


def crvusd_to_reusd(amount):
    """Convert crvUSD to reUSD via crvUSD -> scrvUSD -> reUSD"""
    if amount == 0:
        return 0
    scrvusd_amount = crvusd_to_scrvusd(amount)
    return scrvusd_to_reusd(scrvusd_amount)


def reusd_to_crvusd(amount):
    """Convert reUSD to crvUSD via reUSD -> scrvUSD -> crvUSD"""
    if amount == 0:
        return 0
    scrvusd_amount = reusd_to_scrvusd(amount)
    return scrvusd_to_crvusd(scrvusd_amount)


def reusd_to_sreusd(amount):
    """Convert reUSD to sReUSD via deposit into sReUSD vault"""
    if amount == 0:
        return 0
    return interface.IERC4626(SREUSD_VAULT).convertToShares(amount)


def sreusd_to_reusd(amount):
    """Convert sReUSD to reUSD via redeem from sReUSD vault"""
    if amount == 0:
        return 0
    return interface.IERC4626(SREUSD_VAULT).convertToAssets(amount)
