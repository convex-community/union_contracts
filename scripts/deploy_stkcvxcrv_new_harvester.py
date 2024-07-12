from brownie import (
    accounts,
    interface,
    stkCvxCrvHarvester,
)
from brownie.network.gas.strategies import LinearScalingStrategy
from brownie.network import gas_price

from tests.utils.constants import (
    AIRFORCE_SAFE, CVXCRV, NEW_CVX_CRV_STAKING, CVXCRV_TOKEN,
    AIRFORCE_TREASURY, CRV, CVX, THREECRV_TOKEN,
)


def main():
    publish = True
    gas_strategy = LinearScalingStrategy("5 gwei", "25 gwei", 1.2)
    gas_price(gas_strategy)
    deployer = accounts.load("mainnet-deploy")

    strategy = "0xEC221AE5c62029cB03D91EFf85611A378A1F8883"
    harvester = stkCvxCrvHarvester.deploy(strategy, {"from": deployer}, publish_source=publish)
    harvester.setApprovals({"from": deployer})
    harvester.setPendingOwner(AIRFORCE_SAFE, {"from": deployer})


