from brownie import (
    accounts,
    interface,
    stkCvxCrvVault,
    stkCvxCrvHarvester,
    stkCvxCrvStrategy,
    stkCvxCrvZaps,
)
from brownie.network.gas.strategies import LinearScalingStrategy
from brownie.network import gas_price

from tests.utils.constants import (
    AIRFORCE_SAFE, CVXCRV, NEW_CVX_CRV_STAKING,
)


def main():
    publish = True
    gas_strategy = LinearScalingStrategy("15 gwei", "25 gwei", 1.1)
    gas_price(gas_strategy)
    deployer = accounts.load("mainnet-deploy")
    vault = stkCvxCrvVault.deploy(CVXCRV, {"from": deployer}, publish_source=publish)
    vault.setPlatformFee(400, {"from": deployer})
    vault.setWithdrawalPenalty(25, {"from": deployer})
    vault.setCallIncentive(100, {"from": deployer})
    vault.setPlatform(AIRFORCE_SAFE, {"from": deployer})


    strategy = stkCvxCrvStrategy.deploy(vault, NEW_CVX_CRV_STAKING, {"from": deployer}, publish_source=publish)
    strategy.setApprovals({"from": deployer})
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
