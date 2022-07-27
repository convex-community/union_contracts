from brownie import (
    accounts,
    interface,
    AuraBalVault,
    AuraHandler,
    BBUSDHandler,
    AuraBalStrategy,
    AuraBalZaps,
)

from tests.utils.constants import (
    AURA_BAL_TOKEN,
    AIRFORCE_SAFE,
    AURA_TOKEN,
    BBUSD_TOKEN,
    BAL_TOKEN,
    ADDRESS_ZERO,
)


def main():
    deployer = accounts.load("mainnet-deploy")
    vault = AuraBalVault.deploy(
        AURA_BAL_TOKEN, {"from": deployer}
    )  # , publish_source=True)
    vault.setPlatform(AIRFORCE_SAFE, {"from": deployer})

    strategy = AuraBalStrategy.deploy(
        vault, {"from": deployer}
    )  # , publish_source=True)
    strategy.setApprovals({"from": deployer})
    vault.setStrategy(strategy, {"from": deployer})

    aura_handler = AuraHandler.deploy(
        AURA_TOKEN, strategy, {"from": deployer}
    )  # , publish_source=True)
    aura_handler.setApprovals({"from": deployer})
    bbusd_handler = BBUSDHandler.deploy(
        BBUSD_TOKEN, strategy, {"from": deployer}
    )  # , publish_source=True)

    strategy.addRewardToken(BAL_TOKEN, ADDRESS_ZERO, {"from": deployer})
    strategy.addRewardToken(AURA_TOKEN, aura_handler, {"from": deployer})
    strategy.addRewardToken(BBUSD_TOKEN, bbusd_handler, {"from": deployer})

    zaps = AuraBalZaps.deploy(vault, {"from": deployer})
    zaps.setApprovals({"from": deployer})

    vault.transferOwnership(AIRFORCE_SAFE, {"from": deployer})
    assert vault.owner() == AIRFORCE_SAFE

    strategy.transferOwnership(AIRFORCE_SAFE, {"from": deployer})
    assert vault.owner() == AIRFORCE_SAFE
