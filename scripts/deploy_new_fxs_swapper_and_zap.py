from brownie import accounts, interface, CvxFxsZaps, FXSSwapper
from tests.utils import CRV, CURVE_CRV_ETH_POOL

AIRFORCE_SAFE = "0x9Bc7c6ad7E7Cf3A6fCB58fb21e27752AC1e53f99"


def main():

    deployer = accounts.load("mainnet-deploy")

    swaps = FXSSwapper.deploy("0x853dcbf4dd00dbc6a70002ff87be3671ac966067", {"from": deployer}, publish_source=True)
    swaps.setApprovals({"from": deployer})
    swaps.transferOwnership(AIRFORCE_SAFE, {"from": deployer})

    zaps = CvxFxsZaps.deploy("0xf964b0e3ffdea659c44a5a52bc0b82a24b89ce0e", {"from": deployer}, publish_source=True)
    zaps.setApprovals({"from": deployer})
    zaps.setSwapOption(3, {"from": deployer})

    zaps.transferOwnership(AIRFORCE_SAFE, {"from": deployer})

    assert zaps.owner() == AIRFORCE_SAFE
    assert interface.IERC20(CRV).allowance(zaps, CURVE_CRV_ETH_POOL) == 2**256 - 1
