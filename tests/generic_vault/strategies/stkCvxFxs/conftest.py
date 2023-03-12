import pytest
import brownie
from brownie import (
    stkCvxFxsVault,
    stkCvxFxsHarvester,
    cvxFxsStaking,
    GenericUnionVault,
    stkCvxFxsZaps,
    stkCvxFxsStrategy,
    interface,
)
from ....utils.constants import (
    CURVE_CVXFXS_FXS_POOL,
    AIRFORCE_SAFE,
    CVXFXS,
    CVXFXS_SINGLE_STAKING_CONTRACT, FXS_COMMUNITY, FXS,
)


@pytest.fixture(scope="module")
def staking(owner):
    yield cvxFxsStaking.at(CVXFXS_SINGLE_STAKING_CONTRACT)


@pytest.fixture(scope="module")
def vault(owner):
    vault = stkCvxFxsVault.deploy(CVXFXS, {"from": owner})
    vault.setPlatform(AIRFORCE_SAFE, {"from": owner})
    yield vault


@pytest.fixture(scope="module")
def strategy(owner, vault):
    strategy = stkCvxFxsStrategy.deploy(vault, {"from": owner})
    strategy.setApprovals({"from": owner})
    vault.setStrategy(strategy, {"from": owner})
    yield strategy


@pytest.fixture(scope="module")
def harvester(owner, strategy):
    harvester = stkCvxFxsHarvester.deploy(strategy, {"from": owner})
    strategy.setHarvester(harvester, {"from": owner})
    harvester.setApprovals({"from": owner})
    yield harvester


@pytest.fixture(scope="module")
def zaps(owner, vault):
    zaps = stkCvxFxsZaps.deploy(vault, {"from": owner})
    zaps.setApprovals({"from": owner})
    yield zaps


@pytest.fixture(scope="module", autouse=True)
def distribute_fxs(alice, zaps):

    interface.IERC20(FXS).transfer(alice, 2e23, {"from": FXS_COMMUNITY})
    interface.IERC20(FXS).approve(zaps, 2**256 - 1, {"from": alice})


@pytest.fixture(scope="module", autouse=True)
def distribute_cvxfxs(accounts, vault, harvester):

    for account in accounts[:10]:
        interface.IERC20(CVXFXS).transfer(
            account.address, 1e22, {"from": CURVE_CVXFXS_FXS_POOL}
        )
        interface.IERC20(CVXFXS).approve(vault, 2**256 - 1, {"from": account})
