from brownie import (
    accounts,
    interface,
    CrvUsdSwapper,
    sCrvUsdDistributor,
)
from brownie.network.gas.strategies import LinearScalingStrategy
from brownie.network import gas_price

from tests.utils.constants import (
    AIRFORCE_SAFE, SCRVUSD_VAULT,
    CRVUSD_TOKEN,
)


def main():
    publish = True
    gas_strategy = LinearScalingStrategy("6 gwei", "25 gwei", 1.1)
    gas_price(gas_strategy)
    deployer = accounts.load("mainnet-deploy")

    union_zap = "0xD52Ca71AAfa4d2590aac1E35e3005242dd31e5eD"

    swapper = CrvUsdSwapper.deploy(union_zap, {'from': deployer}, publish_source=publish)
    swapper.setApprovals({"from": deployer})

    merkle = sCrvUsdDistributor.deploy(SCRVUSD_VAULT,
                                       union_zap,
                                       CRVUSD_TOKEN, {"from": deployer}, publish_source=publish)
    merkle.setApprovals({"from": deployer})
    merkle.updateAdmin(AIRFORCE_SAFE, {"from": deployer})

