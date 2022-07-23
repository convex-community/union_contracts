import pytest
import brownie
from brownie import GenericUnionVault, AuraBalStrategy, interface
from ....utils.constants import (
    AIRFORCE_SAFE,
    AURA_BAL_TOKEN,
    AURA_BAL_STAKING,
)


@pytest.fixture(scope="module")
def vault(owner):
    vault = GenericUnionVault.deploy(AURA_BAL_TOKEN, {"from": owner})
    vault.setPlatform(AIRFORCE_SAFE, {"from": owner})
    yield vault


@pytest.fixture(scope="module")
def strategy(owner, vault):
    strategy = AuraBalStrategy.deploy(vault, {"from": owner})
    strategy.setApprovals({"from": owner})
    vault.setStrategy(strategy, {"from": owner})
    yield strategy


"""
@pytest.fixture(scope="module")
def zaps(owner, vault):
    zaps = CvxFxsZaps.deploy(vault, {"from": owner})
    zaps.setApprovals({"from": owner})
    yield zaps
"""


@pytest.fixture(scope="module", autouse=True)
def distribute_fxs_and_lp_tokens(accounts, vault):

    for account in accounts[:10]:
        interface.IERC20(AURA_BAL_TOKEN).transfer(
            account.address, 1e22, {"from": AURA_BAL_STAKING}
        )
        interface.IERC20(AURA_BAL_TOKEN).approve(vault, 2**256 - 1, {"from": account})
