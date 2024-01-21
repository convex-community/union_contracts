from brownie import (
    accounts,
    interface,
    stkCvxPrismaVault,
    stkCvxPrismaStrategy,
    stkCvxPrismaHarvester,
    stkCvxPrismaZaps,
    stkCvxPrismaMerkleDistributor,
    stkCvxPrismaDistributorZaps,
    PrismaSwapper
)
from brownie.network.gas.strategies import LinearScalingStrategy
from brownie.network import gas_price

from tests.utils.constants import (
    AIRFORCE_SAFE, CVXPRISMA,
)


def main():
    union_zap = "0xD52Ca71AAfa4d2590aac1E35e3005242dd31e5eD"
    publish = False
    gas_strategy = LinearScalingStrategy("20 gwei", "35 gwei", 1.1)
    gas_price(gas_strategy)
    deployer = accounts.load("mainnet-deploy")
    vault = stkCvxPrismaVault.at("0x9bfD08D7b3cC40129132A17b4d5B9Ea3351464BD")

    zaps = stkCvxPrismaZaps.deploy(vault, {"from": deployer}, publish_source=publish)
    zaps.setApprovals({"from": deployer})

    prisma_distributor = stkCvxPrismaMerkleDistributor.at(
        "0xF09320Ed7Db384Cab7fce9ea9947436a806754d3"
    )
    prisma_distributor.updateZap(zaps, {"from": deployer})

    distributor_zaps = stkCvxPrismaDistributorZaps.deploy(
        zaps, prisma_distributor, vault, {"from": deployer}, publish_source=publish
    )
    distributor_zaps.setApprovals({"from": deployer})

    prisma_distributor.updateAdmin(AIRFORCE_SAFE, {"from": deployer})
    assert vault.owner() == AIRFORCE_SAFE

