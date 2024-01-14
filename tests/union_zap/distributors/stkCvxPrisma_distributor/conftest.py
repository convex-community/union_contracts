import pytest
import brownie
from brownie import (
    stkCvxPrismaVault,
    stkCvxPrismaDistributorZaps,
    stkCvxPrismaStrategy,
    stkCvxPrismaZaps,
    stkCvxPrismaHarvester,
    StakingRewards,
    stkCvxPrismaMerkleDistributor,
    interface,
)
from tests.utils.constants import AIRFORCE_SAFE, CURVE_CVXPRISMA_PRISMA_POOL, CVXPRISMA, PRISMA, PRISMA_LOCKER


@pytest.fixture(scope="module")
def prisma_vault(owner):
    vault = stkCvxPrismaVault.deploy(CVXPRISMA, {"from": owner})
    vault.setPlatform(AIRFORCE_SAFE, {"from": owner})
    yield vault


@pytest.fixture(scope="module")
def prisma_strategy(owner, prisma_vault):
    strategy = stkCvxPrismaStrategy.deploy(prisma_vault, {"from": owner})
    strategy.setApprovals({"from": owner})
    prisma_vault.setStrategy(strategy, {"from": owner})
    yield strategy


@pytest.fixture(scope="module")
def prisma_harvester(owner, prisma_strategy):
    harvester = stkCvxPrismaHarvester.deploy(prisma_strategy, {"from": owner})
    prisma_strategy.setHarvester(harvester, {"from": owner})
    prisma_harvester.setApprovals({"from": owner})
    yield prisma_harvester


@pytest.fixture(scope="module")
def prisma_zaps(owner, prisma_vault):
    zaps = stkCvxPrismaZaps.deploy(prisma_vault, {"from": owner})
    zaps.setApprovals({"from": owner})
    yield zaps


@pytest.fixture(scope="module")
def prisma_distributor(alice, owner, prisma_zaps, prisma_vault):
    prisma_distributor = stkCvxPrismaMerkleDistributor.deploy(
        prisma_vault, alice, prisma_zaps, {"from": owner}
    )
    prisma_distributor.setApprovals({"from": owner})
    yield prisma_distributor


@pytest.fixture(scope="module")
def distributor_zaps(prisma_distributor, owner, prisma_zaps, prisma_vault):
    distributor_zaps = stkCvxPrismaDistributorZaps.deploy(
        prisma_zaps, prisma_distributor, prisma_vault, {"from": owner}
    )
    distributor_zaps.setApprovals({"from": owner})
    yield distributor_zaps


@pytest.fixture(scope="module", autouse=True)
def distribute_cvx_prisma(prisma_distributor, owner):
    amount = 1e22
    interface.IERC20(PRISMA).transfer(
        prisma_distributor, amount, {"from": PRISMA_LOCKER}
    )
    prisma_distributor.stake({"from": owner})


@pytest.fixture(scope="module", autouse=True)
def add_output_token(prisma_distributor, owner):
    amount = 1e22
    interface.IERC20(PRISMA).transfer(
        prisma_distributor, amount, {"from": PRISMA_LOCKER}
    )
    prisma_distributor.stake({"from": owner})
