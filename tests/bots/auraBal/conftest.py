import pytest
from brownie import (
    BotZap,
    interface,
    chain,
    AuraBalVault,
    AuraBalStrategy,
    BBUSDHandler,
    AuraHandler,
)

from tests.utils import AURA_BAL_TOKEN
from tests.utils.constants import (
    AIRFORCE_SAFE,
    AURA_TOKEN,
    BBUSD_TOKEN,
    AURABAL_TOKEN,
    AURABAL_REWARDS,
    BAL_TOKEN,
    ADDRESS_ZERO,
)


@pytest.fixture(scope="session")
def alice(accounts):
    yield accounts[1]


@pytest.fixture(scope="session")
def bob(accounts):
    yield accounts[2]


@pytest.fixture(scope="session")
def charlie(accounts):
    yield accounts[3]


@pytest.fixture(scope="session")
def dave(accounts):
    yield accounts[4]


@pytest.fixture(scope="session")
def erin(accounts):
    yield accounts[5]


@pytest.fixture(scope="session")
def owner(accounts):
    yield accounts[0]


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
    handler = BBUSDHandler.deploy(BBUSD_TOKEN, strategy, {"from": owner})
    yield handler


@pytest.fixture(scope="module")
def bot(owner, vault):
    bot = BotZap.deploy(vault, {"from": owner})
    bot.set_approvals({"from": owner})
    yield bot


@pytest.fixture(scope="module", autouse=True)
def set_handlers(owner, strategy, aura_handler, bbusd_handler):
    strategy.addRewardToken(BAL_TOKEN, ADDRESS_ZERO, {"from": owner})
    strategy.addRewardToken(AURA_TOKEN, aura_handler, {"from": owner})
    strategy.addRewardToken(BBUSD_TOKEN, bbusd_handler, {"from": owner})


@pytest.fixture(scope="module", autouse=True)
def deposit_funds(alice, vault, strategy):
    aurabal = interface.IERC20(AURABAL_TOKEN)
    aurabal.transfer(alice, 1e22, {"from": AURABAL_REWARDS})
    aurabal.approve(vault, 2**256 - 1, {"from": alice})
    vault.depositAll(alice, {"from": alice})
    chain.sleep(60 * 60 * 24 * 30)
    chain.mine(1)
