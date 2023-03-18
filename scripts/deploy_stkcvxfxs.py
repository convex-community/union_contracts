from brownie import (
    accounts,
    interface,
    stkCvxFxsVault,
    stkCvxFxsStrategy,
    stkCvxFxsHarvester,
    stkCvxFxsZaps,
    stkCvxFxsMerkleDistributor,
    stkCvxFxsDistributorZaps,
    stkCvxFxsMigration
)
from brownie.network.gas.strategies import LinearScalingStrategy
from brownie.network import gas_price

from tests.utils.constants import (
    AIRFORCE_SAFE, CVXFXS,
)


def main():
    publish = False
    gas_strategy = LinearScalingStrategy("20 gwei", "35 gwei", 1.1)
    gas_price(gas_strategy)
    deployer = accounts.load("mainnet-deploy")
    vault = stkCvxFxsVault.deploy(CVXFXS, {"from": deployer}, publish_source=publish)
    vault.setPlatformFee(350, {"from": deployer})
    vault.setWithdrawalPenalty(25, {"from": deployer})
    vault.setCallIncentive(100, {"from": deployer})
    vault.setPlatform(AIRFORCE_SAFE, {"from": deployer})

    strategy = stkCvxFxsStrategy.deploy(vault, {"from": deployer}, publish_source=publish)
    strategy.setApprovals({"from": deployer})
    vault.setStrategy(strategy, {"from": deployer})

    harvester = stkCvxFxsHarvester.deploy(strategy, {"from": deployer}, publish_source=publish)
    strategy.setHarvester(harvester, {"from": deployer})
    harvester.setApprovals({"from": deployer})
    harvester.setSwapOption(3, {"from": deployer})
    harvester.setPendingOwner(AIRFORCE_SAFE, {"from": deployer})

    zaps = stkCvxFxsZaps.deploy(vault, {"from": deployer}, publish_source=publish)
    zaps.setApprovals({"from": deployer})

    union_zap = "0x853dCBF4dd00DBC6A70002fF87Be3671Ac966067"
    fxs_distributor = stkCvxFxsMerkleDistributor.deploy(
        vault, union_zap, zaps, {"from": deployer}, publish_source=publish
    )
    fxs_distributor.setApprovals({"from": deployer})

    distributor_zaps = stkCvxFxsDistributorZaps.deploy(
        zaps, fxs_distributor, vault, {"from": deployer}, publish_source=publish
    )
    distributor_zaps.setApprovals({"from": deployer})

    migration = stkCvxFxsMigration.deploy({"from": deployer}, publish_source=publish)

    vault.transferOwnership(AIRFORCE_SAFE, {"from": deployer})
    assert vault.owner() == AIRFORCE_SAFE

    strategy.transferOwnership(AIRFORCE_SAFE, {"from": deployer})
    assert vault.owner() == AIRFORCE_SAFE
