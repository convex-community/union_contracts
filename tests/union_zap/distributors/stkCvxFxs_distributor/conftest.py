import pytest
import brownie
from brownie import (
    stkCvxFxsVault,
    stkCvxFxsDistributorZaps,
    stkCvxFxsStrategy,
    stkCvxFxsZaps,
    stkCvxFxsHarvester,
    StakingRewards,
    stkCvxFxsMerkleDistributor,
    stkCvxFxsMigration,
    interface,
)
from tests.utils.constants import AIRFORCE_SAFE, CURVE_CVXFXS_FXS_POOL, CVXFXS, FXS


@pytest.fixture(scope="module")
def fxs_vault(owner):
    vault = stkCvxFxsVault.deploy(CVXFXS, {"from": owner})
    vault.setPlatform(AIRFORCE_SAFE, {"from": owner})
    yield vault


@pytest.fixture(scope="module")
def fxs_strategy(owner, fxs_vault):
    strategy = stkCvxFxsStrategy.deploy(fxs_vault, {"from": owner})
    strategy.setApprovals({"from": owner})
    fxs_vault.setStrategy(strategy, {"from": owner})
    yield strategy


@pytest.fixture(scope="module")
def fxs_harvester(owner, fxs_strategy):
    harvester = stkCvxFxsHarvester.deploy(fxs_strategy, {"from": owner})
    fxs_strategy.setHarvester(harvester, {"from": owner})
    fxs_harvester.setApprovals({"from": owner})
    yield fxs_harvester


@pytest.fixture(scope="module")
def fxs_zaps(owner, fxs_vault):
    zaps = stkCvxFxsZaps.deploy(fxs_vault, {"from": owner})
    zaps.setApprovals({"from": owner})
    yield zaps


@pytest.fixture(scope="module")
def fxs_distributor(alice, owner, fxs_zaps, fxs_vault):
    fxs_distributor = stkCvxFxsMerkleDistributor.deploy(
        fxs_vault, alice, fxs_zaps, {"from": owner}
    )
    fxs_distributor.setApprovals({"from": owner})
    yield fxs_distributor


@pytest.fixture(scope="module")
def distributor_zaps(fxs_distributor, owner, fxs_zaps, fxs_vault):
    distributor_zaps = stkCvxFxsDistributorZaps.deploy(
        fxs_zaps, fxs_distributor, fxs_vault, {"from": owner}
    )
    distributor_zaps.setApprovals({"from": owner})
    yield distributor_zaps


@pytest.fixture(scope="module", autouse=True)
def distribute_cvx_fxs(fxs_distributor, owner):
    amount = 1e22
    interface.IERC20(FXS).transfer(
        fxs_distributor, amount, {"from": CURVE_CVXFXS_FXS_POOL}
    )
    fxs_distributor.stake({"from": owner})


@pytest.fixture(scope="module")
def migration(owner):
    yield stkCvxFxsMigration.deploy({"from": owner})
