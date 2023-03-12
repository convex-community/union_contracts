import brownie
import pytest
from brownie import interface
from decimal import Decimal

from ....utils import cvxfxs_balance
from ....utils.constants import (
    ADDRESS_ZERO,
    SPELL,
    SUSHI_ROUTER,
    WETH,
)
from ....utils.cvxfxs import (
    eth_to_fxs,
    fxs_to_cvxfxs,
)


@pytest.mark.parametrize("lock", [True, False])
def test_deposit_from_fxs(fn_isolation, lock, alice, zaps, vault, strategy):

    alice_initial_balance = cvxfxs_balance(alice)

    amount = int(1e23)

    with brownie.reverts():
        zaps.depositFromFxs(amount, 0, ADDRESS_ZERO, lock, {"from": alice})

    cvxfxs_from_fxs = amount if lock else fxs_to_cvxfxs(amount)
    tx = zaps.depositFromFxs(amount, 0, alice, lock, {"from": alice})
    assert vault.balanceOfUnderlying(alice) == cvxfxs_from_fxs
    assert vault.balanceOf(alice) == cvxfxs_from_fxs

    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000
    retrievable = amount * (1 - withdrawal_penalty)
    vault.withdrawAll(alice, {"from": alice})
    assert cvxfxs_balance(alice) > alice_initial_balance


@pytest.mark.parametrize("option", [0, 1, 2, 3])
def test_deposit_from_eth(fn_isolation, option, alice, zaps, owner, vault, strategy):

    amount = 1e18

    zaps.setSwapOption(option, {"from": owner})
    with brownie.reverts():
        zaps.depositFromEth(0, ADDRESS_ZERO, False, {"value": amount, "from": alice})

    cvxfxs_amount = fxs_to_cvxfxs(eth_to_fxs(amount, option))

    zaps.depositFromEth(0, alice, False, {"value": amount, "from": alice})

    assert vault.balanceOfUnderlying(alice) == cvxfxs_amount
    assert vault.balanceOf(alice) == cvxfxs_amount


def test_deposit_from_sushi(fn_isolation, alice, zaps, owner, vault, strategy):
    zaps.setSwapOption(0, {"from": owner})

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

    cvxfxs_amount = fxs_to_cvxfxs(eth_to_fxs(eth_amount, 0))

    zaps.depositViaUniV2EthPair(
        amount, 0, SUSHI_ROUTER, SPELL, alice, False, {"from": alice}
    )

    assert vault.balanceOfUnderlying(alice) == cvxfxs_amount
    assert vault.balanceOf(alice) == cvxfxs_amount
