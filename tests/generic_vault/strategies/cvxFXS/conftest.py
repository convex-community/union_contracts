import pytest
import brownie
from brownie import GenericUnionVault, CvxFxsStrategy, interface
from ....utils.constants import (
    CVXCRV,
    VE_FXS,
    FXS,
    CURVE_CVXFXS_FXS_POOL,
    CURVE_CVXFXS_FXS_LP_TOKEN,
    AIRFORCE_SAFE,
)


@pytest.fixture(scope="module")
def vault(owner):
    vault = GenericUnionVault.deploy(CURVE_CVXFXS_FXS_LP_TOKEN, {"from": owner})
    vault.setPlatform(AIRFORCE_SAFE, {"from": owner})
    yield vault


@pytest.fixture(scope="module")
def strategy(owner, vault):
    strategy = CvxFxsStrategy.deploy(vault, {"from": owner})
    strategy.setApprovals({"from": owner})
    vault.setStrategy(strategy, {"from": owner})
    yield strategy


@pytest.fixture(scope="module", autouse=True)
def distribute_fxs_and_lp_tokens(accounts, vault):

    for account in accounts[:10]:
        interface.IERC20(FXS).transfer(account.address, 1e23, {"from": VE_FXS})
        interface.IERC20(FXS).approve(
            CURVE_CVXFXS_FXS_POOL, 2 ** 256 - 1, {"from": account}
        )
        interface.ICurveV2Pool(CURVE_CVXFXS_FXS_POOL).add_liquidity(
            [5e22, 0], 0, {"from": account}
        )
        assert interface.IERC20(CURVE_CVXFXS_FXS_LP_TOKEN).balanceOf(account) > 0
        interface.IERC20(CURVE_CVXFXS_FXS_LP_TOKEN).approve(
            vault, 2 ** 256 - 1, {"from": account}
        )
