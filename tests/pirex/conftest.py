import pytest
from brownie import (
    PCvxZaps,
    PirexClaims,
    interface,
)
from ..utils.constants import (
    PIREX_CVX_VAULT,
    PIREX_CVX,
    CVX,
    CVX_STAKING_CONTRACT,
    CLAIM_AMOUNT,
    VOTIUM_DISTRIBUTOR,
    VOTIUM_OWNER,
    TOKENS,
    WETH,
    PIREX_CVX_STRATEGY,
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


@pytest.fixture(scope="module")
def union_contract(owner):
    claims = PirexClaims.deploy({"from": owner})
    claims.setApprovals({"from": owner})
    yield claims


@pytest.fixture(scope="module")
def pirex_strategy(owner, union_contract):
    strategy = interface.IPirexStrategy(PIREX_CVX_STRATEGY)
    strategy.setDistributor(union_contract.address, {"from": strategy.owner()})
    yield strategy
