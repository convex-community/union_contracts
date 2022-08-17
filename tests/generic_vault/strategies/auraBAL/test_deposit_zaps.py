import brownie
import pytest
from brownie import chain, interface

from ....utils import aurabal_balance, approx
from ....utils.aurabal import estimate_wethbal_lp_tokens_received, get_blp_to_aurabal
from ....utils.constants import (
    ADDRESS_ZERO,
    SUSHI_ROUTER,
    WETH,
    BAL_TOKEN,
    BAL_VAULT,
    FXS,
)


@pytest.mark.parametrize("lock", [False, True])
def test_deposit_from_underlying(fn_isolation, alice, zaps, vault, strategy, lock):

    alice_initial_balance = aurabal_balance(alice)

    interface.IERC20(WETH).transfer(alice, 2e21, {"from": BAL_VAULT})
    interface.IERC20(BAL_TOKEN).transfer(alice, 2e21, {"from": BAL_VAULT})

    interface.IERC20(WETH).approve(zaps, 2**256 - 1, {"from": alice})
    interface.IERC20(BAL_TOKEN).approve(zaps, 2**256 - 1, {"from": alice})
    amount = int(1e21)

    with brownie.reverts():
        zaps.depositFromUnderlyingAssets(
            [amount, 0], amount * 2, alice, lock, {"from": alice}
        )
    with brownie.reverts():
        zaps.depositFromUnderlyingAssets(
            [amount, 0], 0, ADDRESS_ZERO, lock, {"from": alice}
        )

    lp_tokens_amount_from_bal = estimate_wethbal_lp_tokens_received(strategy, amount, 0)
    received_aurabal_from_bal = (
        lp_tokens_amount_from_bal
        if lock
        else get_blp_to_aurabal(lp_tokens_amount_from_bal)
    )

    zaps.depositFromUnderlyingAssets([amount, 0], 0, alice, lock, {"from": alice})
    assert approx(vault.balanceOfUnderlying(alice), received_aurabal_from_bal, 1e-3)
    assert vault.balanceOf(alice) == vault.balanceOfUnderlying(alice)

    lp_tokens_amount_from_weth = estimate_wethbal_lp_tokens_received(
        strategy, 0, amount
    )
    received_aurabal_from_bal_from_weth = (
        lp_tokens_amount_from_weth
        if lock
        else get_blp_to_aurabal(lp_tokens_amount_from_weth)
    )

    zaps.depositFromUnderlyingAssets([0, amount], 0, alice, lock, {"from": alice})
    assert approx(
        vault.balanceOfUnderlying(alice),
        received_aurabal_from_bal + received_aurabal_from_bal_from_weth,
        1e-3,
    )
    assert approx(
        vault.balanceOf(alice),
        received_aurabal_from_bal + received_aurabal_from_bal_from_weth,
        1e-3,
    )

    lp_tokens_from_both = estimate_wethbal_lp_tokens_received(strategy, amount, amount)
    received_aurabal_from_both = (
        lp_tokens_from_both if lock else get_blp_to_aurabal(lp_tokens_from_both)
    )

    zaps.depositFromUnderlyingAssets([amount, amount], 0, alice, lock, {"from": alice})
    assert approx(
        vault.balanceOfUnderlying(alice),
        received_aurabal_from_bal
        + received_aurabal_from_bal_from_weth
        + received_aurabal_from_both,
        1e-3,
    )
    assert approx(
        vault.balanceOf(alice),
        received_aurabal_from_bal
        + received_aurabal_from_bal_from_weth
        + received_aurabal_from_both,
        1e-3,
    )

    vault.withdrawAll(alice, {"from": alice})
    assert aurabal_balance(alice) > alice_initial_balance


@pytest.mark.parametrize("lock", [False, True])
def test_deposit_from_eth(fn_isolation, alice, zaps, owner, vault, strategy, lock):

    amount = int(1e18)

    with brownie.reverts():
        zaps.depositFromEth(0, ADDRESS_ZERO, lock, {"value": amount, "from": alice})

    lp_tokens_from_eth = estimate_wethbal_lp_tokens_received(strategy, 0, amount)
    received_aurabal = (
        lp_tokens_from_eth if lock else get_blp_to_aurabal(lp_tokens_from_eth)
    )
    zaps.depositFromEth(0, alice, lock, {"value": amount, "from": alice})

    assert approx(vault.balanceOfUnderlying(alice), received_aurabal, 1e-3)
    assert vault.balanceOf(alice) == vault.balanceOfUnderlying(alice)


@pytest.mark.parametrize("lock", [False, True])
def test_deposit_from_sushi(fn_isolation, alice, zaps, owner, vault, strategy, lock):

    amount = int(1e21)
    interface.IERC20(FXS).transfer(alice.address, 2e21, {"from": FXS})
    interface.IERC20(FXS).approve(zaps, 2**256 - 1, {"from": alice})

    with brownie.reverts():
        zaps.depositViaUniV2EthPair(
            amount, 0, SUSHI_ROUTER, FXS, ADDRESS_ZERO, lock, {"from": alice}
        )

    eth_amount = interface.IUniV2Router(SUSHI_ROUTER).getAmountsOut(
        amount, [FXS, WETH]
    )[-1]

    lp_tokens_from_eth = estimate_wethbal_lp_tokens_received(strategy, 0, eth_amount)
    received_aurabal = (
        lp_tokens_from_eth if lock else get_blp_to_aurabal(lp_tokens_from_eth)
    )

    zaps.depositViaUniV2EthPair(
        amount, 0, SUSHI_ROUTER, FXS, alice, lock, {"from": alice}
    )

    assert approx(vault.balanceOfUnderlying(alice), received_aurabal, 1e-3)
    assert vault.balanceOf(alice) == vault.balanceOfUnderlying(alice)
