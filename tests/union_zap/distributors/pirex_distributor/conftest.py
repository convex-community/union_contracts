import pytest
import brownie
from brownie import (
    CVXMerkleDistributor,
    PirexDistributorZaps,
    PCvxZaps,
    interface,
)
from tests.utils.constants import (
    PIREX_CVX_VAULT,
    CVX,
    PIREX_CVX,
    CVX_STAKING_CONTRACT,
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
def cvx_vault(owner):
    vault = interface.IERC4626(PIREX_CVX_VAULT)
    yield vault


@pytest.fixture(scope="module")
def pirex_cvx(owner):
    pcvx = interface.IPirexCVX(PIREX_CVX)
    yield pcvx


@pytest.fixture(scope="module")
def cvx_distributor(owner, cvx_vault, union_contract, alice):
    merkle = CVXMerkleDistributor.deploy(cvx_vault, alice, CVX, {"from": owner})
    merkle.setApprovals({"from": owner})
    yield merkle


@pytest.fixture(scope="module")
def cvx_zaps(owner):
    zaps = PCvxZaps.deploy({"from": owner})
    zaps.setApprovals({"from": owner})
    yield zaps


@pytest.fixture(scope="module")
def distributor_zaps(fxs_distributor, owner, cvx_distributor, cvx_zaps, cvx_vault):
    distributor_zaps = PirexDistributorZaps.deploy(
        cvx_zaps, cvx_distributor, cvx_vault, {"from": owner}
    )
    distributor_zaps.setApprovals({"from": owner})
    yield distributor_zaps


@pytest.fixture(scope="module", autouse=True)
def distribute_cvx(cvx_distributor, owner):
    amount = 1e24
    interface.IERC20(CVX).transfer(
        cvx_distributor, amount, {"from": CVX_STAKING_CONTRACT}
    )
    cvx_distributor.stake({"from": owner})
