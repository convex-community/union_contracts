import brownie
import pytest
from pytest_lazyfixture import lazy_fixture

from brownie import interface
from tests.utils.constants import (
    CURVE_CVXPRISMA_PRISMA_POOL,
    PRISMA,
)
from tests.utils.cvxprisma import prisma_to_cvxprisma


@pytest.mark.parametrize("caller", [lazy_fixture("owner"), lazy_fixture("alice")])
def test_stake(fn_isolation, prisma_distributor, prisma_vault, caller):
    amount = 1e22
    vault_initial_balance = prisma_vault.balanceOf(prisma_distributor)
    interface.IERC20(PRISMA).transfer(
        prisma_distributor, amount, {"from": CURVE_CVXPRISMA_PRISMA_POOL}
    )
    cvxprisma_received = prisma_to_cvxprisma(amount)
    prisma_distributor.stake({"from": caller})
    assert (
        prisma_vault.balanceOf(prisma_distributor) == cvxprisma_received + vault_initial_balance
    )
    assert (
        prisma_vault.balanceOfUnderlying(prisma_distributor)
        == cvxprisma_received + vault_initial_balance
    )


def test_stake_slippage(fn_isolation, prisma_distributor, prisma_vault, owner):
    amount = 1e22
    interface.IERC20(PRISMA).transfer(
        prisma_distributor, amount, {"from": CURVE_CVXPRISMA_PRISMA_POOL}
    )
    prisma_distributor.setSlippage(20000, {"from": owner})
    with brownie.reverts('Exchange resulted in fewer coins than expected'):
        prisma_distributor.stake({"from": owner})


def test_stake_access(fn_isolation, prisma_distributor, prisma_vault, bob):
    amount = 1e22
    interface.IERC20(PRISMA).transfer(
        prisma_distributor, amount, {"from": CURVE_CVXPRISMA_PRISMA_POOL}
    )
    with brownie.reverts("Admin or depositor only"):
        prisma_distributor.stake({"from": bob})
