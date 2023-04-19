import pytest
import brownie
from brownie import (
    stkCvxCrvMerkleDistributor,
    stkCvxCrvDistributorZaps,
    stkCvxCrvZaps,
    stkCvxCrvMigration,
    stkCvxCrvVault,
    stkCvxCrvStrategy,
    stkCvxCrvHarvester,
    interface,
)
from tests.utils.constants import (
    CVXCRV_TOKEN,
    CVXCRV,
    CURVE_CVXCRV_CRV_POOL,
    AIRFORCE_SAFE,
    NEW_CVX_CRV_STAKING,
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
    vault = stkCvxCrvVault.deploy(CVXCRV, {"from": owner})
    vault.setPlatform(AIRFORCE_SAFE, {"from": owner})
    yield vault


@pytest.fixture(scope="module")
def wrapper(owner):
    yield interface.ICvxCrvStaking(NEW_CVX_CRV_STAKING)


@pytest.fixture(scope="module")
def strategy(owner, vault, wrapper):
    strategy = stkCvxCrvStrategy.deploy(vault, wrapper, {"from": owner})
    vault.setStrategy(strategy, {"from": owner})
    strategy.setApprovals({"from": owner})
    yield strategy


@pytest.fixture(scope="module")
def harvester(owner, strategy):
    harvester = stkCvxCrvHarvester.deploy(strategy, {"from": owner})
    harvester.setApprovals({"from": owner})
    yield harvester


@pytest.fixture(scope="module")
def distributor(owner, vault, alice):
    merkle = stkCvxCrvMerkleDistributor.deploy(
        vault, alice, CVXCRV_TOKEN, {"from": owner}
    )
    merkle.setApprovals({"from": owner})
    yield merkle


@pytest.fixture(scope="module")
def vault_zaps(owner, vault):
    zaps = stkCvxCrvZaps.deploy(vault, {"from": owner})
    zaps.setApprovals({"from": owner})
    yield zaps


@pytest.fixture(scope="module")
def migration(owner):
    yield stkCvxCrvMigration.deploy({"from": owner})


@pytest.fixture(scope="module")
def distributor_zaps(owner, distributor, vault_zaps, vault):
    distributor_zaps = stkCvxCrvDistributorZaps.deploy(
        vault_zaps, distributor, vault, {"from": owner}
    )
    distributor_zaps.setApprovals({"from": owner})
    yield distributor_zaps


@pytest.fixture(scope="module", autouse=True)
def set_harvester(owner, strategy, harvester):
    strategy.setHarvester(harvester, {"from": owner})


@pytest.fixture(scope="module", autouse=True)
def distribute_cvxcrv(distributor, owner, strategy, harvester):
    interface.IERC20(CVXCRV).transfer(
        distributor, 1e24, {"from": CURVE_CVXCRV_CRV_POOL}
    )
    distributor.stake({"from": owner})
