import brownie
import pytest
from pytest_lazyfixture import lazy_fixture

from brownie import interface
from tests.utils.constants import (
    CURVE_CVXFXS_FXS_POOL,
    FXS,
)
from tests.utils.cvxfxs import fxs_to_cvxfxs


@pytest.mark.parametrize("caller", [lazy_fixture("owner"), lazy_fixture("alice")])
def test_stake(fn_isolation, fxs_distributor, fxs_vault, caller):
    amount = 1e22
    vault_initial_balance = fxs_vault.balanceOf(fxs_distributor)
    interface.IERC20(FXS).transfer(
        fxs_distributor, amount, {"from": CURVE_CVXFXS_FXS_POOL}
    )
    cvxfxs_received = fxs_to_cvxfxs(amount)
    fxs_distributor.stake({"from": caller})
    assert (
        fxs_vault.balanceOf(fxs_distributor) == cvxfxs_received + vault_initial_balance
    )
    assert (
        fxs_vault.balanceOfUnderlying(fxs_distributor)
        == cvxfxs_received + vault_initial_balance
    )


def test_stake_slippage(fn_isolation, fxs_distributor, fxs_vault, owner):
    amount = 1e22
    interface.IERC20(FXS).transfer(
        fxs_distributor, amount, {"from": CURVE_CVXFXS_FXS_POOL}
    )
    fxs_distributor.setSlippage(20000, {"from": owner})
    with brownie.reverts("Slippage"):
        fxs_distributor.stake({"from": owner})


def test_stake_access(fn_isolation, fxs_distributor, fxs_vault, bob):
    amount = 1e22
    interface.IERC20(FXS).transfer(
        fxs_distributor, amount, {"from": CURVE_CVXFXS_FXS_POOL}
    )
    with brownie.reverts("Admin or depositor only"):
        fxs_distributor.stake({"from": bob})
