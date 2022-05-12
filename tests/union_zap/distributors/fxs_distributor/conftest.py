import pytest
import brownie
from brownie import (
    GenericUnionVault,
    DistributorZaps,
    CvxFxsStrategy,
    CvxFxsZaps,
    StakingRewards,
    FXSMerkleDistributor,
    interface,
)
from tests.utils.constants import (
    CURVE_CVXFXS_FXS_LP_TOKEN,
    AIRFORCE_SAFE, FXS, CURVE_CVXFXS_FXS_POOL,
)


@pytest.fixture(scope="module")
def fxs_vault(owner):
    vault = GenericUnionVault.deploy(CURVE_CVXFXS_FXS_LP_TOKEN, {"from": owner})
    vault.setPlatform(AIRFORCE_SAFE, {"from": owner})
    yield vault


@pytest.fixture(scope="module")
def fxs_strategy(owner, fxs_vault):
    strategy = CvxFxsStrategy.deploy(fxs_vault, {"from": owner})
    strategy.setApprovals({"from": owner})
    fxs_vault.setStrategy(strategy, {"from": owner})
    yield strategy


@pytest.fixture(scope="module")
def fxs_zaps(owner, fxs_vault):
    zaps = CvxFxsZaps.deploy(fxs_vault, {"from": owner})
    zaps.setApprovals({"from": owner})
    yield zaps


@pytest.fixture(scope="module")
def fxs_distributor(alice, owner, fxs_zaps, fxs_vault):
    fxs_distributor = FXSMerkleDistributor.deploy(
        fxs_vault, alice, fxs_zaps, {"from": owner}
    )
    fxs_distributor.setApprovals({"from": owner})
    yield fxs_distributor


@pytest.fixture(scope="module")
def distributor_zaps(fxs_distributor, owner, fxs_zaps, fxs_vault):
    distributor_zaps = DistributorZaps.deploy(
        fxs_zaps, fxs_distributor, fxs_vault, {"from": owner}
    )
    fxs_distributor.setApprovals({"from": owner})
    yield distributor_zaps


@pytest.fixture(scope="module", autouse=True)
def distribute_cvx_fxs(fxs_distributor, owner):
    amount = 1e22
    interface.IERC20(FXS).transfer(
        fxs_distributor, amount, {"from": CURVE_CVXFXS_FXS_POOL}
    )
    fxs_distributor.stake({"from": owner})
