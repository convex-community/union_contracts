from brownie import (
    accounts,
    interface,
    stkCvxCrvHarvester,
    stkCvxCrvZaps,
    stkCvxCrvDistributorZaps,
)
from brownie.network.gas.strategies import LinearScalingStrategy
from brownie.network import gas_price
from tests.utils.constants import (
    AIRFORCE_SAFE
)


def main():
    publish = True
    gas_strategy = LinearScalingStrategy("15 gwei", "35 gwei", 1.2)
    gas_price(gas_strategy)
    deployer = accounts.load("mainnet-deploy")
    strategy = "0xEC221AE5c62029cB03D91EFf85611A378A1F8883"
    harvester = stkCvxCrvHarvester.deploy(strategy, {"from": deployer}, publish_source=publish)
    harvester.setApprovals({"from": deployer})
    harvester.setPendingOwner(AIRFORCE_SAFE, {"from": deployer})

    vault = "0xde2bEF0A01845257b4aEf2A2EAa48f6EAeAfa8B7"
    zaps = stkCvxCrvZaps.deploy(vault, {"from": deployer}, publish_source=publish)
    zaps.setApprovals({"from": deployer})

    merkle = "0x2c5e808fCA6D8299ce194E12ed728f0fDbbF06c8"
    distributor_zaps = stkCvxCrvDistributorZaps.deploy(
        zaps, merkle, vault, {"from": deployer}, publish_source=publish
    )
    distributor_zaps.setApprovals({"from": deployer})