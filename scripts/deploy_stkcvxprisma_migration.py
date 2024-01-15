from brownie import (
    accounts,
    interface,
    stkCvxPrismaMigration
)
from brownie.network.gas.strategies import LinearScalingStrategy
from brownie.network import gas_price


def main():
    union_vault = "0x9bfD08D7b3cC40129132A17b4d5B9Ea3351464BD"
    publish = True
    gas_strategy = LinearScalingStrategy("20 gwei", "35 gwei", 1.1)
    gas_price(gas_strategy)
    deployer = accounts.load("mainnet-deploy")
    migration = stkCvxPrismaMigration.deploy(union_vault, {"from": deployer}, publish_source=publish)
    migration.setApprovals({"from": deployer})
