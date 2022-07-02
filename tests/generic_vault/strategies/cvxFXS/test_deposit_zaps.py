import brownie
import pytest
from brownie import chain, interface

from ....utils import cvxfxs_lp_balance
from ....utils.constants import (
    CVXFXS,
    FXS,
    FXS_COMMUNITY,
    CURVE_CVXFXS_FXS_POOL,
    ADDRESS_ZERO,
    CRV,
    CVX,
    CURVE_CRV_ETH_POOL,
    CURVE_CVX_ETH_POOL,
    CURVE_CVXFXS_FXS_LP_TOKEN,
    SPELL,
    SUSHI_ROUTER,
    WETH,
)
from ....utils.cvxfxs import (
    estimate_lp_tokens_received,
    get_crv_to_eth_amount,
    get_cvx_to_eth_amount,
    eth_fxs_curve,
    eth_fxs_uniswap,
    eth_fxs_unistable,
)


def test_deposit_from_underlying(fn_isolation, alice, zaps, vault, strategy):

    alice_initial_balance = cvxfxs_lp_balance(alice)

    interface.IERC20(CVXFXS).transfer(alice, 2e23, {"from": CURVE_CVXFXS_FXS_POOL})
    interface.IERC20(FXS).transfer(alice, 2e23, {"from": FXS_COMMUNITY})

    interface.IERC20(CVXFXS).approve(zaps, 2**256 - 1, {"from": alice})
    interface.IERC20(FXS).approve(zaps, 2**256 - 1, {"from": alice})
    amount = 1e23

    with brownie.reverts():
        zaps.depositFromUnderlyingAssets(
            [amount, 0], amount * 2, alice, {"from": alice}
        )
    with brownie.reverts():
        zaps.depositFromUnderlyingAssets([amount, 0], 0, ADDRESS_ZERO, {"from": alice})

    lp_tokens_from_fxs = estimate_lp_tokens_received(amount)
    zaps.depositFromUnderlyingAssets([amount, 0], 0, alice, {"from": alice})
    assert vault.balanceOfUnderlying(alice) == lp_tokens_from_fxs
    assert vault.balanceOf(alice) == lp_tokens_from_fxs

    lp_tokens_from_cvxfxs = estimate_lp_tokens_received(0, amount)
    zaps.depositFromUnderlyingAssets([0, amount], 0, alice, {"from": alice})
    assert (
        vault.balanceOfUnderlying(alice) == lp_tokens_from_fxs + lp_tokens_from_cvxfxs
    )
    assert vault.balanceOf(alice) == lp_tokens_from_fxs + lp_tokens_from_cvxfxs

    lp_tokens_from_both = estimate_lp_tokens_received(amount, amount)
    zaps.depositFromUnderlyingAssets([amount, amount], 0, alice, {"from": alice})
    assert (
        vault.balanceOfUnderlying(alice)
        == lp_tokens_from_fxs + lp_tokens_from_cvxfxs + lp_tokens_from_both
    )
    assert (
        vault.balanceOf(alice)
        == lp_tokens_from_fxs + lp_tokens_from_cvxfxs + lp_tokens_from_both
    )

    vault.withdrawAll(alice, {"from": alice})
    assert cvxfxs_lp_balance(alice) > alice_initial_balance


@pytest.mark.parametrize("amount_crv", [0, 1e21])
@pytest.mark.parametrize("amount_cvx", [0, 1e21])
@pytest.mark.parametrize("amount_lp", [0, 1e21])
def test_deposit_with_rewards(
    fn_isolation, alice, zaps, owner, vault, strategy, amount_crv, amount_cvx, amount_lp
):
    zaps.setSwapOption(0, {"from": owner})

    print(f"CVX: {amount_cvx}, CRV: {amount_crv}, LP: {amount_lp}")

    if (amount_crv + amount_cvx + amount_lp) == 0:
        with brownie.reverts("cheap"):
            zaps.depositWithRewards(
                amount_lp, amount_crv, amount_cvx, 0, alice, {"from": alice}
            )

        chain.revert()
        return

    amount = 1e23

    interface.IERC20(CVX).transfer(alice, amount, {"from": CURVE_CVX_ETH_POOL})
    interface.IERC20(CRV).transfer(alice, amount, {"from": CURVE_CRV_ETH_POOL})

    interface.IERC20(CVX).approve(zaps, 2**256 - 1, {"from": alice})
    interface.IERC20(CRV).approve(zaps, 2**256 - 1, {"from": alice})
    interface.IERC20(CURVE_CVXFXS_FXS_LP_TOKEN).approve(
        zaps, 2**256 - 1, {"from": alice}
    )

    """
    disabled for crashing RPC trace
    with brownie.reverts():
        zaps.depositWithRewards(
            amount_lp, amount_crv, amount_cvx, 2 ** 256 - 1, alice, {"from": alice}
        )
    """
    with brownie.reverts():
        zaps.depositWithRewards(
            amount_lp, amount_crv, amount_cvx, 0, ADDRESS_ZERO, {"from": alice}
        )

    eth_amount = get_cvx_to_eth_amount(amount_cvx) + get_crv_to_eth_amount(amount_crv)
    fxs_amount = eth_fxs_curve(eth_amount)

    lp_tokens_from_fxs = estimate_lp_tokens_received(fxs_amount)
    zaps.depositWithRewards(
        amount_lp, amount_crv, amount_cvx, 0, alice, {"from": alice}
    )

    assert vault.balanceOfUnderlying(alice) == lp_tokens_from_fxs + amount_lp
    assert vault.balanceOf(alice) == lp_tokens_from_fxs + amount_lp


@pytest.mark.parametrize("option", [0, 1, 2])
def test_deposit_from_eth(fn_isolation, option, alice, zaps, owner, vault, strategy):
    zaps.setSwapOption(0, {"from": owner})

    amount = 1e18

    zaps.setSwapOption(option, {"from": owner})
    with brownie.reverts():
        zaps.depositFromEth(0, ADDRESS_ZERO, {"value": amount, "from": alice})

    if option == 0:
        fxs_amount = eth_fxs_curve(amount)
    elif option == 1:
        fxs_amount = eth_fxs_uniswap(amount)
    elif option == 2:
        fxs_amount = eth_fxs_unistable(amount)

    lp_tokens_from_fxs = estimate_lp_tokens_received(fxs_amount)
    zaps.depositFromEth(0, alice, {"value": amount, "from": alice})

    assert vault.balanceOfUnderlying(alice) == lp_tokens_from_fxs
    assert vault.balanceOf(alice) == lp_tokens_from_fxs


def test_deposit_from_sushi(fn_isolation, alice, zaps, owner, vault, strategy):
    zaps.setSwapOption(0, {"from": owner})

    amount = 1e18
    interface.IERC20(SPELL).transfer(alice.address, 2e22, {"from": SPELL})
    interface.IERC20(SPELL).approve(zaps, 2**256 - 1, {"from": alice})

    with brownie.reverts():
        zaps.depositViaUniV2EthPair(
            amount, 0, SUSHI_ROUTER, SPELL, ADDRESS_ZERO, {"from": alice}
        )

    eth_amount = interface.IUniV2Router(SUSHI_ROUTER).getAmountsOut(
        amount, [SPELL, WETH]
    )[-1]

    fxs_amount = eth_fxs_curve(eth_amount)

    lp_tokens_from_fxs = estimate_lp_tokens_received(fxs_amount)
    zaps.depositViaUniV2EthPair(amount, 0, SUSHI_ROUTER, SPELL, alice, {"from": alice})

    assert vault.balanceOfUnderlying(alice) == lp_tokens_from_fxs
    assert vault.balanceOf(alice) == lp_tokens_from_fxs
