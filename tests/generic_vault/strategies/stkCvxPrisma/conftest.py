import pytest
import brownie
from brownie import (
    stkCvxPrismaVault,
    stkCvxPrismaHarvester,
    cvxPrismaStaking,
    GenericUnionVault,
    stkCvxPrismaZaps,
    stkCvxPrismaStrategy,
    interface,
)
from ....utils.constants import (
    CURVE_CVXPRISMA_PRISMA_POOL,
    AIRFORCE_SAFE,
    CVXPRISMA,
    CVXPRISMA_STAKING_CONTRACT,
    PRISMA_LOCKER,
    PRISMA,
)


@pytest.fixture(scope="module")
def staking(owner):
    yield cvxPrismaStaking.at(CVXPRISMA_STAKING_CONTRACT)


@pytest.fixture(scope="module")
def vault(owner):
    vault = stkCvxPrismaVault.deploy(CVXPRISMA, {"from": owner})
    vault.setPlatform(AIRFORCE_SAFE, {"from": owner})
    yield vault


@pytest.fixture(scope="module")
def strategy(owner, vault):
    strategy = stkCvxPrismaStrategy.deploy(vault, {"from": owner})
    strategy.setApprovals({"from": owner})
    vault.setStrategy(strategy, {"from": owner})
    yield strategy


@pytest.fixture(scope="module")
def harvester(owner, strategy):
    harvester = stkCvxPrismaHarvester.deploy(strategy, {"from": owner})
    strategy.setHarvester(harvester, {"from": owner})
    harvester.setApprovals({"from": owner})
    yield harvester


@pytest.fixture(scope="module")
def second_harvester(owner, strategy):
    harvester = stkCvxPrismaHarvester.deploy(strategy, {"from": owner})
    harvester.setApprovals({"from": owner})
    yield harvester


@pytest.fixture(scope="module")
def zaps(owner, vault):
    zaps = stkCvxPrismaZaps.deploy(vault, {"from": owner})
    zaps.setApprovals({"from": owner})
    yield zaps


@pytest.fixture(scope="module", autouse=True)
def distribute_fxs(alice, zaps):

    interface.IERC20(PRISMA).transfer(alice, 2e23, {"from": PRISMA_LOCKER})
    interface.IERC20(PRISMA).approve(zaps, 2**256 - 1, {"from": alice})


@pytest.fixture(scope="module", autouse=True)
def distribute_cvxfxs(accounts, vault, harvester):

    for account in accounts[:10]:
        interface.IERC20(CVXPRISMA).transfer(
            account.address, 1e22, {"from": CURVE_CVXPRISMA_PRISMA_POOL}
        )
        interface.IERC20(CVXPRISMA).approve(vault, 2**256 - 1, {"from": account})
