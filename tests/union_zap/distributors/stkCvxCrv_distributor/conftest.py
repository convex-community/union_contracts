import pytest
import brownie
from brownie import (
    stkCvxCrvMerkleDistributor,
    stkCvxCrvDistributorZaps,
    stkCvxCrvZaps,
    stkCvxCrvMigration,
    interface,
)
from tests.utils.constants import (
    STAKED_CVXCRV_VAULT, CVXCRV_TOKEN, STAKED_CVXCRV_ZAPS, CVXCRV, CURVE_CVXCRV_CRV_POOL,
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
    vault = interface.IGenericVault(STAKED_CVXCRV_VAULT)
    yield vault


@pytest.fixture(scope="module")
def distributor(owner, vault, alice):
    merkle = stkCvxCrvMerkleDistributor.deploy(vault, alice, CVXCRV_TOKEN, {"from": owner})
    merkle.setApprovals({"from": owner})
    yield merkle


@pytest.fixture(scope="module")
def vault_zaps(owner):
    yield stkCvxCrvZaps.at(STAKED_CVXCRV_ZAPS)


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
def distribute_cvxcrv(distributor, owner):
    interface.IERC20(CVXCRV).transfer(
        distributor, 1e24, {"from": CURVE_CVXCRV_CRV_POOL}
    )
    distributor.stake({"from": owner})
