import pytest
from brownie import AirdropDistributor, interface
from web3 import Web3

from ...utils.airdrop.prisma import PRISMA_CLAIMS
from ...utils.constants import PRISMA, PRISMA_LOCKER
from ...utils.merkle import OrderedMerkleTree


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
def prisma_claim_tree():
    data = [
        {"user": Web3.toChecksumAddress(k), "amount": v}
        for k, v in PRISMA_CLAIMS.items()
    ]
    tree = OrderedMerkleTree(data)
    return tree


@pytest.fixture(scope="module")
def airdrop(prisma_claim_tree, owner):
    airdrop = AirdropDistributor.deploy(PRISMA, 6, {"from": owner})
    interface.IERC20(PRISMA).transfer(airdrop, 100000 * 1e18, {"from": PRISMA_LOCKER})
    airdrop.updateMerkleRoot(prisma_claim_tree.get_root(), True, {"from": owner})
    yield airdrop
