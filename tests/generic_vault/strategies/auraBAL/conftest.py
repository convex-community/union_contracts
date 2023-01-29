import pytest
import brownie
from brownie import (
    AuraBalVault,
    AuraBalStrategy,
    AuraBalZaps,
    interface,
    BBUSDHandlerv2,
    AuraHandler,
)
from ....utils.constants import (
    AIRFORCE_SAFE,
    AURA_BAL_TOKEN,
    AURA_BAL_STAKING,
    AURA_TOKEN,
    BBUSD_TOKEN,
    BAL_TOKEN,
    ADDRESS_ZERO,
)


@pytest.fixture(scope="module")
def vault(owner):
    vault = AuraBalVault.deploy(AURA_BAL_TOKEN, {"from": owner})
    vault.setPlatform(AIRFORCE_SAFE, {"from": owner})
    yield vault


@pytest.fixture(scope="module")
def strategy(owner, vault):
    strategy = AuraBalStrategy.deploy(vault, {"from": owner})
    strategy.setApprovals({"from": owner})
    vault.setStrategy(strategy, {"from": owner})
    yield strategy


@pytest.fixture(scope="module")
def aura_handler(owner, vault, strategy):
    handler = AuraHandler.deploy(AURA_TOKEN, strategy, {"from": owner})
    handler.setApprovals({"from": owner})
    yield handler


@pytest.fixture(scope="module")
def bbusd_handler(owner, vault, strategy):
    handler = BBUSDHandlerv2.deploy(BBUSD_TOKEN, strategy, {"from": owner})
    yield handler


@pytest.fixture(scope="module")
def zaps(owner, vault):
    zaps = AuraBalZaps.deploy(vault, {"from": owner})
    zaps.setApprovals({"from": owner})
    yield zaps


@pytest.fixture(scope="module", autouse=True)
def set_handlers(owner, strategy, aura_handler, bbusd_handler):
    strategy.addRewardToken(BAL_TOKEN, ADDRESS_ZERO, {"from": owner})
    strategy.addRewardToken(AURA_TOKEN, aura_handler, {"from": owner})
    strategy.addRewardToken(BBUSD_TOKEN, bbusd_handler, {"from": owner})


@pytest.fixture(scope="module", autouse=True)
def distribute_aurabal_tokens(accounts, vault):

    for account in accounts[:10]:
        interface.IERC20(AURA_BAL_TOKEN).transfer(
            account.address, 1e22, {"from": AURA_BAL_STAKING}
        )
        interface.IERC20(AURA_BAL_TOKEN).approve(vault, 2**256 - 1, {"from": account})
