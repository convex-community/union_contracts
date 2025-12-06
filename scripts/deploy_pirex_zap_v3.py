from brownie import (
    accounts,
    interface,
    PirexDistributorZaps,
)
from brownie.network import gas_price
from brownie.network.gas.strategies import LinearScalingStrategy

from tests.utils.constants import PIREX_CVX_VAULT


def main():
    deployer = accounts.load("mainnet-deploy")
    gas_strategy = LinearScalingStrategy("1 gwei", "5 gwei", 0.2)
    gas_price(gas_strategy)

    distributor_zaps = PirexDistributorZaps.deploy(
        "0xB192908E533FC64109A20eE7d056175a24f17a55", #ucvx_zaps,
        "0x9dA701a9b76E0dd136d3508cb60A4c436Dda25e4", #ucvx_distributor,
        PIREX_CVX_VAULT,
        {"from": deployer},
        publish_source=True,
    )
    distributor_zaps.setApprovals({"from": deployer})