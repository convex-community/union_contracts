from brownie import accounts, interface, CvxFxsZaps, CvxFxsStrategy, GenericUnionVault

from tests.utils import CURVE_CVXFXS_FXS_LP_TOKEN, CRV, CURVE_CRV_ETH_POOL

AIRFORCE_SAFE = "0x9Bc7c6ad7E7Cf3A6fCB58fb21e27752AC1e53f99"


def main():

    deployer = accounts.load("mainnet-deploy")
    vault = GenericUnionVault.deploy(CURVE_CVXFXS_FXS_LP_TOKEN, {"from": deployer})
    vault.setPlatform(AIRFORCE_SAFE, {"from": deployer})

    strategy = CvxFxsStrategy.deploy(vault, {"from": deployer})
    strategy.setApprovals({"from": deployer})
    strategy.setSwapOption(2, {"from": deployer})
    vault.setStrategy(strategy, {"from": deployer})

    zaps = CvxFxsZaps.deploy(vault, {"from": deployer})
    zaps.setApprovals({"from": deployer})
    zaps.setSwapOption(2, {"from": deployer})

    zaps.transferOwnership(AIRFORCE_SAFE, {"from": deployer})
    strategy.transferOwnership(AIRFORCE_SAFE, {"from": deployer})
    vault.transferOwnership(AIRFORCE_SAFE, {"from": deployer})

    assert zaps.owner() == AIRFORCE_SAFE
    assert vault.owner() == AIRFORCE_SAFE
    assert strategy.owner() == AIRFORCE_SAFE
    assert vault.strategy() == strategy
    assert strategy.swapOption() == 2
    assert zaps.swapOption() == 2
    assert interface.IERC20(CRV).allowance(zaps, CURVE_CRV_ETH_POOL) == 2 ** 256 - 1

    GenericUnionVault.publish_source(vault)
    CvxFxsStrategy.publish_source(strategy)
    CvxFxsZaps.publish_source(zaps)
