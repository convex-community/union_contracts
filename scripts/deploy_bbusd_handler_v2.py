from brownie import (
    accounts,
    interface,
    BBUSDHandlerv2,
)
from brownie.network.gas.strategies import LinearScalingStrategy
from brownie.network import gas_price

from tests.utils.constants import (
    BBUSD_TOKEN,
)


def main():
    gas_strategy = LinearScalingStrategy("12 gwei", "25 gwei", 1.1)
    gas_price(gas_strategy)
    deployer = accounts.load("mainnet-deploy")

    strategy = "0x4B0987beF3F966354C6EcD22F6D844d621EE5077"

    BBUSDHandlerv2.deploy(
        BBUSD_TOKEN, strategy, {"from": deployer}, publish_source=True
    )

