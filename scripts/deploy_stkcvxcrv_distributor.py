from brownie import (
    accounts,
    interface,
    stkCvxCrvMigration,
    stkCvxCrvDistributorZaps,
    stkCvxCrvMerkleDistributor,
)
from brownie.network.gas.strategies import LinearScalingStrategy
from brownie.network import gas_price

from tests.utils.constants import (
    AIRFORCE_SAFE, CVXCRV, NEW_CVX_CRV_STAKING, STAKED_CVXCRV_VAULT, STAKED_CVXCRV_ZAPS, CVXCRV_TOKEN,
)


def main():
    publish = False
    gas_strategy = LinearScalingStrategy("15 gwei", "25 gwei", 1.1)
    gas_price(gas_strategy)
    deployer = accounts.load("mainnet-deploy")

    vault = STAKED_CVXCRV_VAULT
    vault_zaps = STAKED_CVXCRV_ZAPS
    union_zap = "0x853dCBF4dd00DBC6A70002fF87Be3671Ac966067"

    migration = stkCvxCrvMigration.deploy({"from": deployer}, publish_source=publish)

    merkle = stkCvxCrvMerkleDistributor.deploy(vault, union_zap, CVXCRV_TOKEN, {"from": deployer}, publish_source=publish)
    merkle.setApprovals({"from": deployer})

    distributor_zaps = stkCvxCrvDistributorZaps.deploy(
        vault_zaps, merkle, vault, {"from": deployer}, publish_source=publish
    )
    distributor_zaps.setApprovals({"from": deployer})

    migration.transferOwnership(AIRFORCE_SAFE, {"from": deployer})
    merkle.updateAdmin(AIRFORCE_SAFE, {"from": deployer})

