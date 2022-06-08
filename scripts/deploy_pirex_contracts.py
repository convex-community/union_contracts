from brownie import (
    accounts,
    interface,
    PirexClaims,
    CVXMerkleDistributor,
    PCvxZaps,
    PirexDistributorZaps,
)

from tests.utils import CRV, CURVE_CRV_ETH_POOL
from tests.utils.constants import (
    CVX,
    FXS,
    CURVE_CVX_ETH_POOL,
    CURVE_FXS_ETH_POOL,
    PIREX_CVX_VAULT,
)

CVXCRV = "0x62B9c7356A2Dc64a1969e19C23e4f579F9810Aa7"
AIRFORCE_SAFE = "0x9Bc7c6ad7E7Cf3A6fCB58fb21e27752AC1e53f99"
UNION_ZAP = "0x7A7f79c5706716bae853c1b96e36538C7EAA4925"


def main():
    deployer = accounts.load("mainnet-deploy")
    zap = PirexClaims.deploy({"from": deployer}, publish_source=True)
    zap.setApprovals({"from": deployer})

    ucvx_zaps = PCvxZaps.deploy({"from": deployer}, publish_source=True)
    ucvx_zaps.setApprovals({"from": deployer})

    ucvx_distributor = CVXMerkleDistributor.deploy(
        PIREX_CVX_VAULT, UNION_ZAP, CVX, {"from": deployer}, publish_source=True
    )
    ucvx_distributor.setApprovals({"from": deployer})
    ucvx_distributor.updateAdmin(AIRFORCE_SAFE, {"from": deployer})

    distributor_zaps = PirexDistributorZaps.deploy(
        ucvx_zaps,
        ucvx_distributor,
        PIREX_CVX_VAULT,
        {"from": deployer},
        publish_source=True,
    )
    distributor_zaps.setApprovals({"from": deployer})

    zap.transferOwnership(AIRFORCE_SAFE, {"from": deployer})
    assert zap.owner() == AIRFORCE_SAFE
