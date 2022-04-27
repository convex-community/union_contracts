from brownie import accounts, interface, FXSMerkleDistributor, FXSSwapper, MerkleDistributor, UnionZap

from tests.utils import CRV, CURVE_CRV_ETH_POOL
from tests.utils.constants import CVX, FXS, CURVE_CVX_ETH_POOL, CURVE_FXS_ETH_POOL

CVXCRV = "0x62B9c7356A2Dc64a1969e19C23e4f579F9810Aa7"
AIRFORCE_SAFE = "0x9Bc7c6ad7E7Cf3A6fCB58fb21e27752AC1e53f99"
ADDRESS_ZERO = "0x0000000000000000000000000000000000000000"
UCRV_DISTRIBUTOR = "0xA83043Df401346A67eddEb074679B4570b956183"
CVXCRV_DEPOSIT = "0x8014595F2AB54cD7c604B00E9fb932176fDc86Ae"
CRV_TOKEN = "0xD533a949740bb3306d119CC777fa900bA034cd52"
FXS_VAULT = "0xF964b0E3FfdeA659c44a5a52bc0B82A24b89CE0E"
FXS_ZAPS = "0x63f0797015489D407FC2AC7E3891467e1eD0166c"

def main():
    deployer = accounts.load("mainnet-deploy")
    zap = UnionZap.deploy({"from": deployer}, publish_source=True)
    zap.setApprovals({"from": deployer})
    assert interface.IERC20(CRV).allowance(zap, CVXCRV_DEPOSIT) == 2 ** 256 - 1

    swaps = FXSSwapper.deploy(zap, {"from": deployer}, publish_source=True)
    swaps.setApprovals({"from": deployer})

    fxs_distributor = FXSMerkleDistributor.deploy(
        FXS_VAULT, zap, FXS_ZAPS, {"from": deployer}, publish_source=True
    )
    fxs_distributor.setApprovals({"from": deployer})

    zap.updateOutputToken(
        CRV, [CURVE_CRV_ETH_POOL, ADDRESS_ZERO, UCRV_DISTRIBUTOR], {"from": deployer}
    )
    zap.updateOutputToken(
        CVX, [CURVE_CVX_ETH_POOL, ADDRESS_ZERO, fxs_distributor], {"from": deployer}
    )
    zap.updateOutputToken(
        FXS, [CURVE_FXS_ETH_POOL, swaps, fxs_distributor], {"from": deployer}
    )

    zap.transferOwnership(AIRFORCE_SAFE, {"from": deployer})
    assert zap.owner() == AIRFORCE_SAFE