import pytest
import brownie
from brownie import cvxFxsStaking, GenericUnionVault, StkCvxFxsZaps, StkCvxFxsStrategy, interface
from ....utils.constants import (
    VE_FXS,
    FXS,
    CURVE_CVXFXS_FXS_POOL,
    CURVE_CVXFXS_FXS_LP_TOKEN,
    AIRFORCE_SAFE, CVXFXS,
)


@pytest.fixture(scope="module")
def staking(owner):
    yield cvxFxsStaking.deploy({"from": owner})


@pytest.fixture(scope="module")
def vault(owner):
    vault = GenericUnionVault.deploy(CVXFXS, {"from": owner})
    vault.setPlatform(AIRFORCE_SAFE, {"from": owner})
    yield vault


@pytest.fixture(scope="module")
def strategy(owner, vault, staking):
    strategy = StkCvxFxsStrategy.deploy(vault, staking, {"from": owner})
    strategy.setApprovals({"from": owner})
    vault.setStrategy(strategy, {"from": owner})
    yield strategy


@pytest.fixture(scope="module")
def zaps(owner, vault):
    zaps = StkCvxFxsZaps.deploy(vault, {"from": owner})
    zaps.setApprovals({"from": owner})
    yield zaps


@pytest.fixture(scope="module", autouse=True)
def distribute_cvxfxs(accounts, vault):

    for account in accounts[:10]:
        interface.IERC20(CVXFXS).transfer(account.address, 1e22, {"from": CURVE_CVXFXS_FXS_POOL})
        interface.IERC20(CVXFXS).approve(
            vault, 2**256 - 1, {"from": account}
        )
