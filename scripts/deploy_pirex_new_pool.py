from brownie import (
    accounts,
    interface,
    PirexClaims,
    PCvxZaps,
    CVXMerkleDistributor,
    PirexDistributorZaps,
    PirexMigrationV1
)

from tests.utils import CVX
from tests.utils.constants import PIREX_CVX_VAULT

UNION_ZAP = "0x853dcbf4dd00dbc6a70002ff87be3671ac966067"
AIRFORCE_SAFE = "0x9Bc7c6ad7E7Cf3A6fCB58fb21e27752AC1e53f99"


def main():
    publish = True
    deployer = accounts.load("mainnet-deploy")
    claim = PirexClaims.deploy({"from": deployer}, publish_source=publish)
    claim.setApprovals({"from": deployer})

    ucvx_zaps = PCvxZaps.deploy({"from": deployer}, publish_source=publish)
    ucvx_zaps.setApprovals({"from": deployer})

    ucvx_distributor = CVXMerkleDistributor.deploy(
        PIREX_CVX_VAULT, UNION_ZAP, CVX, {"from": deployer}, publish_source=publish
    )
    ucvx_distributor.setApprovals({"from": deployer})
    ucvx_distributor.updateAdmin(AIRFORCE_SAFE, {"from": deployer})

    distributor_zaps = PirexDistributorZaps.deploy(
        ucvx_zaps,
        ucvx_distributor,
        PIREX_CVX_VAULT,
        {"from": deployer},
        publish_source=publish,
    )
    distributor_zaps.setApprovals({"from": deployer})

    migrator = PirexMigrationV1.deploy({"from": deployer})
    migrator.transferOwnership(AIRFORCE_SAFE, {"from": deployer})

    claim.transferOwnership(AIRFORCE_SAFE, {"from": deployer})
    assert claim.owner() == AIRFORCE_SAFE