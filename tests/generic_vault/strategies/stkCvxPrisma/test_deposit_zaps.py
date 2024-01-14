import brownie
import pytest
from brownie import interface, stkCvxPrismaZaps, GenericUnionVault
from decimal import Decimal

from ....utils import cvxprisma_balance
from ....utils.constants import (
    ADDRESS_ZERO,
    SPELL,
    SUSHI_ROUTER,
    WETH,
)
from ....utils.cvxprisma import (
    eth_to_prisma,
    prisma_to_cvxprisma,
)


@pytest.mark.parametrize("lock", [True, False])
def test_deposit_from_prisma(fn_isolation, lock, alice, zaps, vault, strategy):

    alice_initial_balance = cvxprisma_balance(alice)

    amount = int(1e22)

    with brownie.reverts():
        zaps.depositFromPrisma(amount, 0, ADDRESS_ZERO, lock, {"from": alice})

    cvxprisma_from_prisma = amount if lock else prisma_to_cvxprisma(amount)
    tx = zaps.depositFromPrisma(amount, 0, alice, lock, {"from": alice})
    assert vault.balanceOfUnderlying(alice) == cvxprisma_from_prisma
    assert vault.balanceOf(alice) == cvxprisma_from_prisma
    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000
    retrievable = amount * (1 - withdrawal_penalty)
    vault.withdrawAll(alice, {"from": alice})
    assert cvxprisma_balance(alice) > alice_initial_balance


def test_deposit_from_eth(fn_isolation, alice, zaps, owner, vault, strategy):

    amount = 1e18

    with brownie.reverts():
        zaps.depositFromEth(0, ADDRESS_ZERO, False, {"value": amount, "from": alice})

    cvxprisma_amount = prisma_to_cvxprisma(eth_to_prisma(amount))

    zaps.depositFromEth(0, alice, False, {"value": amount, "from": alice})

    assert vault.balanceOfUnderlying(alice) == cvxprisma_amount
    assert vault.balanceOf(alice) == cvxprisma_amount


def test_deposit_from_sushi(fn_isolation, alice, zaps, owner, vault, strategy):

    amount = 1e18
    interface.IERC20(SPELL).transfer(alice.address, 2e22, {"from": SPELL})
    interface.IERC20(SPELL).approve(zaps, 2**256 - 1, {"from": alice})

    with brownie.reverts():
        zaps.depositViaUniV2EthPair(
            amount, 0, SUSHI_ROUTER, SPELL, ADDRESS_ZERO, False, {"from": alice}
        )

    eth_amount = interface.IUniV2Router(SUSHI_ROUTER).getAmountsOut(
        amount, [SPELL, WETH]
    )[-1]

    cvxprisma_amount = prisma_to_cvxprisma(eth_to_prisma(eth_amount))

    zaps.depositViaUniV2EthPair(
        amount, 0, SUSHI_ROUTER, SPELL, alice, False, {"from": alice}
    )

    assert vault.balanceOfUnderlying(alice) == cvxprisma_amount
    assert vault.balanceOf(alice) == cvxprisma_amount
