from brownie import (
    accounts,
    interface,
    ReUsdSwapper,
    sReUsdDistributor,
)
from brownie.network.gas.strategies import LinearScalingStrategy
from brownie.network import gas_price

from tests.utils.constants import (
    AIRFORCE_SAFE, SREUSD_VAULT,
    REUSD_TOKEN,
)


def main():
    publish = True
    gas_strategy = LinearScalingStrategy("1 gwei", "5 gwei", 1.1)
    gas_price(gas_strategy)
    deployer = accounts.load("mainnet-deploy")

    union_zap = "0xD52Ca71AAfa4d2590aac1E35e3005242dd31e5eD"

    swapper = ReUsdSwapper.deploy(union_zap, {'from': deployer}, publish_source=publish)
    swapper.setApprovals({"from": deployer})
    print(f"Swapper: {swapper}")

    merkle = sReUsdDistributor.deploy(SREUSD_VAULT,
                                       union_zap,
                                       REUSD_TOKEN, {"from": deployer}, publish_source=publish)
    merkle.setApprovals({"from": deployer})
    merkle.updateAdmin(AIRFORCE_SAFE, {"from": deployer})
    print(f"Distributor: {merkle}")

