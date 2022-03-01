import pytest
from brownie import GenericUnionVault, interface
from ..utils.constants import CVXCRV, ADDRESS_ZERO


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
def dummy_vault(owner):
    vault = GenericUnionVault.deploy(CVXCRV, {"from": owner})
    yield vault
