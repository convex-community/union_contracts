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
    publish = True
    gas_strategy = LinearScalingStrategy("20 gwei", "35 gwei", 1.1)
    gas_price(gas_strategy)
    deployer = accounts.load("mainnet-deploy")
    vault = stkCvxPrismaVault.deploy(CVXPRISMA, {"from": deployer}, publish_source=publish)
    vault.setPlatformFee(350, {"from": deployer})
    vault.setWithdrawalPenalty(25, {"from": deployer})
    vault.setCallIncentive(100, {"from": deployer})
    vault.setPlatform(AIRFORCE_SAFE, {"from": deployer})

    swaps = PrismaSwapper.deploy(union_zap, {"from": deployer}, publish_source=publish)
    swaps.setApprovals({"from": deployer})
    swaps.transferOwnership(AIRFORCE_SAFE, {"from": deployer})

    strategy = stkCvxPrismaStrategy.deploy(vault, {"from": deployer}, publish_source=publish)
    strategy.setApprovals({"from": deployer})
    vault.setStrategy(strategy, {"from": deployer})

    harvester = stkCvxPrismaHarvester.deploy(strategy, {"from": deployer}, publish_source=publish)
    strategy.setHarvester(harvester, {"from": deployer})
    harvester.setApprovals({"from": deployer})
    harvester.setPendingOwner(AIRFORCE_SAFE, {"from": deployer})

    zaps = stkCvxPrismaZaps.deploy(vault, {"from": deployer}, publish_source=publish)
    zaps.setApprovals({"from": deployer})

    prisma_distributor = stkCvxPrismaMerkleDistributor.deploy(
        vault, union_zap, zaps, {"from": deployer}, publish_source=publish
    )
    prisma_distributor.setApprovals({"from": deployer})

    distributor_zaps = stkCvxPrismaDistributorZaps.deploy(
        zaps, prisma_distributor, vault, {"from": deployer}, publish_source=publish
    )
    distributor_zaps.setApprovals({"from": deployer})

    vault.transferOwnership(AIRFORCE_SAFE, {"from": deployer})
    assert vault.owner() == AIRFORCE_SAFE

    strategy.transferOwnership(AIRFORCE_SAFE, {"from": deployer})
    assert strategy.owner() == AIRFORCE_SAFE
