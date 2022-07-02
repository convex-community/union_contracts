import pytest
from brownie import UnionVault, ExtraZaps, MerkleDistributorV2, interface
from ..utils.constants import CVXCRV, CVXCRV_SLP, CURVE_CVXCRV_CRV_POOL, CVXCRV_REWARDS


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
    vault = UnionVault.deploy({"from": owner})
    vault.setApprovals({"from": owner})
    yield vault


@pytest.fixture(scope="module")
def merkle_distributor_v2(owner, vault):
    merkle = MerkleDistributorV2.deploy(vault, vault, {"from": owner})
    merkle.setApprovals({"from": owner})
    yield merkle


@pytest.fixture(scope="module")
def zaps(owner, vault, merkle_distributor_v2):
    zaps = ExtraZaps.deploy(vault, merkle_distributor_v2, {"from": owner})
    zaps.setApprovals({"from": owner})
    yield zaps


@pytest.fixture(scope="module", autouse=True)
def distribute_cvx_crv(accounts, vault, merkle_distributor_v2):
    interface.IERC20(CVXCRV).transfer(
        merkle_distributor_v2, 1e25, {"from": CVXCRV_REWARDS}
    )
    merkle_distributor_v2.stake()

    for account in accounts[:10]:
        interface.IERC20(CVXCRV).transfer(
            account.address, 2e22, {"from": CURVE_CVXCRV_CRV_POOL}
        )

        interface.IERC20(CVXCRV).approve(vault, 2**256 - 1, {"from": account})
