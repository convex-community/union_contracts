from brownie import (
    accounts,
    interface,
    stkCvxCrvVault,
    stkCvxCrvHarvester,
    stkCvxCrvStrategy,
    stkCvxCrvZaps,
    stkCvxCrvMigration,
    stkCvxCrvDistributorZaps,
    stkCvxCrvMerkleDistributor,
)
from brownie.network.gas.strategies import LinearScalingStrategy
from brownie.network import gas_price

from tests.utils.constants import (
    AIRFORCE_SAFE, CVXCRV, NEW_CVX_CRV_STAKING, CVXCRV_TOKEN,
    AIRFORCE_TREASURY, CRV, CVX, THREECRV_TOKEN,
)


def main():
    publish = True
    gas_strategy = LinearScalingStrategy("12 gwei", "25 gwei", 1.2)
    gas_price(gas_strategy)
    deployer = accounts.load("mainnet-deploy")


    vault = stkCvxCrvVault.deploy(CVXCRV, {"from": deployer}, publish_source=publish)
    vault.setPlatformFee(400, {"from": deployer})
    vault.setWithdrawalPenalty(25, {"from": deployer})
    vault.setCallIncentive(100, {"from": deployer})
    vault.setPlatform(AIRFORCE_TREASURY, {"from": deployer})


    strategy = stkCvxCrvStrategy.deploy(vault, NEW_CVX_CRV_STAKING, {"from": deployer}, publish_source=publish)
    strategy.setApprovals({"from": deployer})
    strategy.updateRewardToken(CRV, 1)
    strategy.updateRewardToken(CVX, 1)
    strategy.updateRewardToken(THREECRV_TOKEN, 1)
    vault.setStrategy(strategy, {"from": deployer})

    harvester = stkCvxCrvHarvester.deploy(strategy, {"from": deployer})
    harvester.setApprovals({"from": deployer})
    harvester.setPendingOwner(AIRFORCE_SAFE, {"from": deployer})

    strategy.setHarvester(harvester, {"from": deployer})

    zaps = stkCvxCrvZaps.deploy(vault, {"from": deployer}, publish_source=publish)
    zaps.setApprovals({"from": deployer})

    vault.transferOwnership(AIRFORCE_SAFE, {"from": deployer})
    assert vault.owner() == AIRFORCE_SAFE

    strategy.transferOwnership(AIRFORCE_SAFE, {"from": deployer})
    assert vault.owner() == AIRFORCE_SAFE

    union_zap = "0x853dCBF4dd00DBC6A70002fF87Be3671Ac966067"

    migration = stkCvxCrvMigration.deploy({"from": deployer}, publish_source=publish)

    merkle = stkCvxCrvMerkleDistributor.deploy(vault, union_zap, CVXCRV_TOKEN, {"from": deployer}, publish_source=publish)
    merkle.setApprovals({"from": deployer})

    distributor_zaps = stkCvxCrvDistributorZaps.deploy(
        zaps, merkle, vault, {"from": deployer}, publish_source=publish
    )
    distributor_zaps.setApprovals({"from": deployer})

    migration.transferOwnership(AIRFORCE_SAFE, {"from": deployer})
    merkle.updateAdmin(AIRFORCE_SAFE, {"from": deployer})

