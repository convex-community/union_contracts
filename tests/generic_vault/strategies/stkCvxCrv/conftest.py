import pytest
from brownie import (
    CvxCrvStakingWrapper,
    stkCvxCrvVault,
    stkCvxCrvStrategy,
    stkCvxCrvHarvester,
    interface,
    chain
)

from ....utils.constants import CRV, CURVE_VOTING_ESCROW, CVXCRV, CURVE_CVXCRV_CRV_POOL, AIRFORCE_SAFE


@pytest.fixture(scope="module")
def wrapper(owner):
    yield CvxCrvStakingWrapper.deploy({"from": owner})


@pytest.fixture(scope="module")
def vault(owner):
    vault = stkCvxCrvVault.deploy(CVXCRV, {"from": owner})
    vault.setPlatform(AIRFORCE_SAFE, {"from": owner})
    yield vault


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
def zaps(owner, vault):
    pass


@pytest.fixture(scope="module", autouse=True)
def set_harvester(owner, strategy, harvester):
    strategy.setHarvester(harvester, {"from": owner})


@pytest.fixture(scope="module", autouse=True)
def distribute_crv_and_cvxcrv(accounts, wrapper, vault):

    for account in accounts[:10]:
        interface.IERC20(CRV).transfer(account.address, 1e24, {"from": CURVE_VOTING_ESCROW})
        interface.IERC20(CVXCRV).transfer(account.address, 1e24, {"from": CURVE_CVXCRV_CRV_POOL})
        interface.IERC20(CVXCRV).approve(
            wrapper, 2**256 - 1, {"from": account}
        )
        interface.IERC20(CVXCRV).approve(
            vault, 2**256 - 1, {"from": account}
        )
    for i, account in enumerate(accounts[6:10]):
        wrapper.setRewardWeight(10000 // (i + 1), {'from': account})
        wrapper.stake(1e23, account, {'from': account})

    chain.sleep(60 * 60 * 12)
    chain.mine(1)