import pytest
from brownie import (
    PCvxZaps,
    interface,
)
from ..utils.constants import (
    PIREX_CVX_VAULT,
    PIREX_CVX,
    CVX,
    CVX_STAKING_CONTRACT,
)
from ..utils.merkle import OrderedMerkleTree


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
def cvx_zaps(owner):
    zaps = PCvxZaps.deploy({"from": owner})
    zaps.setApprovals({"from": owner})
    yield zaps


@pytest.fixture(scope="module", autouse=True)
def distribute_cvx(accounts):
    for account in accounts[:10]:
        interface.IERC20(CVX).transfer(
            account.address, 1e24, {"from": CVX_STAKING_CONTRACT}
        )
