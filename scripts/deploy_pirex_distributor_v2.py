from brownie import (
    accounts,
    interface,
    PirexClaims,
    PCvxZaps,
    CVXMerkleDistributor,
    PirexDistributorZaps,
    PirexMigrationV2
)

from brownie.network.gas.strategies import LinearScalingStrategy
from brownie.network import gas_price

from tests.utils import CVX
from tests.utils.constants import PIREX_CVX_VAULT

UNION_ZAP = "0xD52Ca71AAfa4d2590aac1E35e3005242dd31e5eD"
AIRFORCE_SAFE = "0x9Bc7c6ad7E7Cf3A6fCB58fb21e27752AC1e53f99"


def main():
    publish = True
    gas_strategy = LinearScalingStrategy("0.4 gwei", "5 gwei", 0.2)
    gas_price(gas_strategy)

    deployer = accounts.load("mainnet-deploy")

    ucvx_distributor = CVXMerkleDistributor.deploy(
        PIREX_CVX_VAULT, UNION_ZAP, CVX, {"from": deployer}, publish_source=publish
    )
    ucvx_distributor.setApprovals({"from": deployer})
    ucvx_distributor.updateAdmin(AIRFORCE_SAFE, {"from": deployer})


    migrator = PirexMigrationV2.deploy({"from": deployer}, publish_source=publish)
    migrator.transferOwnership(AIRFORCE_SAFE, {"from": deployer})

    claim.transferOwnership(AIRFORCE_SAFE, {"from": deployer})
    assert claim.owner() == AIRFORCE_SAFE