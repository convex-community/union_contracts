import pytest
import brownie
from brownie import (
    stkCvxPrismaVault,
    stkCvxPrismaHarvester,
    cvxPrismaStaking,
    GenericUnionVault,
    stkCvxPrismaZaps,
    stkCvxPrismaStrategy,
    stkCvxPrismaMigration,
    interface,
)
from ....utils.constants import (
    CURVE_CVXPRISMA_PRISMA_POOL,
    AIRFORCE_SAFE,
    CVXPRISMA,
    CVXPRISMA_STAKING_CONTRACT,
    PRISMA_LOCKER,
    PRISMA,
    STABILITY_POOL,
    MKUSD_TOKEN,
    CONVEX_LOCKER,
    CVX,
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


@pytest.fixture(scope="module")
def migration(owner, vault):
    migration = stkCvxPrismaMigration.deploy(vault, {"from": owner})
    migration.setApprovals({"from": owner})
    yield migration


@pytest.fixture(scope="module", autouse=True)
def distribute_prisma(accounts, zaps):

    for account in accounts[:10]:
        interface.IERC20(PRISMA).transfer(account, 2e23, {"from": PRISMA_LOCKER})
        interface.IERC20(PRISMA).approve(zaps, 2**256 - 1, {"from": account})


# Ensure we have enough rewards of each type of token
@pytest.fixture(scope="module", autouse=True)
def distribute_rewards(staking, alice, zaps):
    staking_owner = "0xDd2f2858964c17486E1b8A7E337a5732170E3320"
    staking.approveRewardDistributor(
        PRISMA, PRISMA_LOCKER, True, {"from": staking_owner}
    )
    staking.approveRewardDistributor(CVX, CONVEX_LOCKER, True, {"from": staking_owner})
    staking.approveRewardDistributor(
        MKUSD_TOKEN, STABILITY_POOL, True, {"from": staking_owner}
    )

    interface.IERC20(PRISMA).approve(staking, 2**256 - 1, {"from": PRISMA_LOCKER})
    interface.IERC20(CVX).approve(staking, 2**256 - 1, {"from": CONVEX_LOCKER})
    interface.IERC20(MKUSD_TOKEN).approve(
        staking, 2**256 - 1, {"from": STABILITY_POOL}
    )

    staking.notifyRewardAmount(PRISMA, 2e23, {"from": PRISMA_LOCKER})
    staking.notifyRewardAmount(CVX, 2e23, {"from": CONVEX_LOCKER})
    staking.notifyRewardAmount(MKUSD_TOKEN, 2e23, {"from": STABILITY_POOL})


@pytest.fixture(scope="module", autouse=True)
def distribute_cvxprisma(accounts, vault, harvester):

    for account in accounts[:10]:
        interface.IERC20(CVXPRISMA).transfer(
            account.address, 1e22, {"from": CURVE_CVXPRISMA_PRISMA_POOL}
        )
        interface.IERC20(CVXPRISMA).approve(vault, 2**256 - 1, {"from": account})
