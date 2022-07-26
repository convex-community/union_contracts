import brownie
import pytest
from brownie import chain, interface

from ....utils import aurabal_balance
from ....utils.aurabal import estimate_wethbal_lp_tokens_received
from ....utils.constants import (
    ADDRESS_ZERO,
    SPELL,
    SUSHI_ROUTER,
    WETH,
    BAL_TOKEN,
    BAL_VAULT,
)


def test_deposit_from_underlying(fn_isolation, alice, zaps, vault, strategy):

    alice_initial_balance = aurabal_balance(alice)

    interface.IERC20(WETH).transfer(alice, 2e21, {"from": BAL_VAULT})
    interface.IERC20(BAL_TOKEN).transfer(alice, 2e21, {"from": BAL_VAULT})

    interface.IERC20(WETH).approve(zaps, 2**256 - 1, {"from": alice})
    interface.IERC20(BAL_TOKEN).approve(zaps, 2**256 - 1, {"from": alice})
    amount = int(1e21)

    with brownie.reverts():
        zaps.depositFromUnderlyingAssets(
            [amount, 0], amount * 2, alice, {"from": alice}
        )
    with brownie.reverts():
        zaps.depositFromUnderlyingAssets([amount, 0], 0, ADDRESS_ZERO, {"from": alice})

    lp_tokens_amount_from_bal = estimate_wethbal_lp_tokens_received(strategy, amount, 0)
    zaps.depositFromUnderlyingAssets([amount, 0], 0, alice, {"from": alice})
    assert vault.balanceOfUnderlying(alice) == lp_tokens_amount_from_bal
    assert vault.balanceOf(alice) == lp_tokens_amount_from_bal

    lp_tokens_amount_from_weth = estimate_wethbal_lp_tokens_received(
        strategy, 0, amount
    )
    zaps.depositFromUnderlyingAssets([0, amount], 0, alice, {"from": alice})
    assert (
        vault.balanceOfUnderlying(alice)
        == lp_tokens_amount_from_bal + lp_tokens_amount_from_weth
    )
    assert (
        vault.balanceOf(alice) == lp_tokens_amount_from_bal + lp_tokens_amount_from_weth
    )

    lp_tokens_from_both = estimate_wethbal_lp_tokens_received(strategy, amount, amount)
    zaps.depositFromUnderlyingAssets([amount, amount], 0, alice, {"from": alice})
    assert (
        vault.balanceOfUnderlying(alice)
        == lp_tokens_amount_from_bal + lp_tokens_amount_from_weth + lp_tokens_from_both
    )
    assert (
        vault.balanceOf(alice)
        == lp_tokens_amount_from_bal + lp_tokens_amount_from_weth + lp_tokens_from_both
    )

    vault.withdrawAll(alice, {"from": alice})
    assert aurabal_balance(alice) > alice_initial_balance


def test_deposit_from_eth(fn_isolation, alice, zaps, owner, vault, strategy):

    amount = int(1e18)

    with brownie.reverts():
        zaps.depositFromEth(0, ADDRESS_ZERO, {"value": amount, "from": alice})

    lp_tokens_from_eth = estimate_wethbal_lp_tokens_received(strategy, 0, amount)
    zaps.depositFromEth(0, alice, {"value": amount, "from": alice})

    assert vault.balanceOfUnderlying(alice) == lp_tokens_from_eth
    assert vault.balanceOf(alice) == lp_tokens_from_eth


def test_deposit_from_sushi(fn_isolation, alice, zaps, owner, vault, strategy):

    amount = int(1e18)
    interface.IERC20(SPELL).transfer(alice.address, 2e22, {"from": SPELL})
    interface.IERC20(SPELL).approve(zaps, 2**256 - 1, {"from": alice})

    with brownie.reverts():
        zaps.depositViaUniV2EthPair(
            amount, 0, SUSHI_ROUTER, SPELL, ADDRESS_ZERO, {"from": alice}
        )

    eth_amount = interface.IUniV2Router(SUSHI_ROUTER).getAmountsOut(
        amount, [SPELL, WETH]
    )[-1]

    lp_tokens_from_eth = estimate_wethbal_lp_tokens_received(strategy, 0, eth_amount)
    zaps.depositViaUniV2EthPair(amount, 0, SUSHI_ROUTER, SPELL, alice, {"from": alice})

    assert vault.balanceOfUnderlying(alice) == lp_tokens_from_eth
    assert vault.balanceOf(alice) == lp_tokens_from_eth
