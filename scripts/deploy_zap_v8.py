from brownie import (
    accounts,
    interface,
    FXSMerkleDistributor,
    FXSSwapper,
    MerkleDistributor,
    UnionZap,
    DistributorZaps,
)

from tests.utils import CRV, CURVE_CRV_ETH_POOL
from tests.utils.constants import CVX, FXS, CURVE_CVX_ETH_POOL, CURVE_FXS_ETH_POOL

CVXCRV = "0x62B9c7356A2Dc64a1969e19C23e4f579F9810Aa7"
AIRFORCE_SAFE = "0x9Bc7c6ad7E7Cf3A6fCB58fb21e27752AC1e53f99"
ADDRESS_ZERO = "0x0000000000000000000000000000000000000000"
UCRV_DISTRIBUTOR = "0x2c5e808fCA6D8299ce194E12ed728f0fDbbF06c8"
UCVX_DISTRIBUTOR = "0x27A11054b62C29c166F3FAb2b0aC708043b0CB49"
UFXS_DISTRIBUTOR = "0x5682a28919389B528AE74dd627e0d632cA7e398C"
FXS_SWAPPER = "0x80617E6a0Fa8E018CEB6ddB9037999B6bb7F9B2B"
CVXCRV_DEPOSIT = "0x8014595F2AB54cD7c604B00E9fb932176fDc86Ae"
CRV_TOKEN = "0xD533a949740bb3306d119CC777fa900bA034cd52"


def main():
    deployer = accounts.load("mainnet-deploy")
    zap = UnionZap.deploy({"from": deployer}, publish_source=True)
    zap.setApprovals({"from": deployer})
    assert interface.IERC20(CRV).allowance(zap, CVXCRV_DEPOSIT) == 2**256 - 1

    zap.updateOutputToken(
        CRV, [CURVE_CRV_ETH_POOL, ADDRESS_ZERO, UCRV_DISTRIBUTOR], {"from": deployer}
    )
    zap.updateOutputToken(
        CVX, [CURVE_CVX_ETH_POOL, ADDRESS_ZERO, UCVX_DISTRIBUTOR], {"from": deployer}
    )
    zap.updateOutputToken(
        FXS, [CURVE_FXS_ETH_POOL, FXS_SWAPPER, UFXS_DISTRIBUTOR], {"from": deployer}
    )

    zap.transferOwnership(AIRFORCE_SAFE, {"from": deployer})
    assert zap.owner() == AIRFORCE_SAFE
