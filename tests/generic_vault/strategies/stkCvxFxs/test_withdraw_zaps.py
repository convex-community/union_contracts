import brownie
import pytest
from brownie import interface, chain
from decimal import Decimal

from ....utils.constants import (
    TRICRYPTO,
    USDT_TOKEN,
    CURVE_CVX_ETH_POOL,
    CVX,
    CVXFXS,
    FXS,
    SUSHI_ROUTER,
    WETH,
    SPELL,
    ADDRESS_ZERO,
    CONVEX_LOCKER,
)
from ....utils.cvxfxs import (
    estimate_underlying_received,
    fxs_eth_curve,
    fxs_eth_uniswap,
    fxs_eth_unistable,
    fxs_eth_unicurve1,
    fxs_to_eth,
    cvxfxs_to_fxs,
)

OPTIONS = ["Curve", "UniV3EthToFxs", "UniV3EthFraxFxs", "UniCurveEthFraxUsdcFxs"]


@pytest.mark.parametrize("option", [0, 1, 2, 3])
def test_claim_as_usdt(
    fn_isolation, alice, bob, charlie, owner, vault, strategy, zaps, option
):
    amount = int(1e21)
    zaps.setSwapOption(option, {"from": owner})
    for i, account in enumerate([alice, bob, charlie]):
        vault.deposit(account, amount, {"from": account})

    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000

    cvxfxs_amount = amount * (1 - withdrawal_penalty)
    fxs_amount = cvxfxs_to_fxs(cvxfxs_amount)
    eth_amount = fxs_to_eth(fxs_amount, option)
    print("\033[95m" + f"Harvested {OPTIONS[option]}: {eth_amount * 1e-18} ETH")

    usdt_amount = interface.ICurveV2Pool(TRICRYPTO).get_dy(2, 0, eth_amount)
    vault.approve(zaps, 2**256 - 1, {"from": alice})

    tx = zaps.claimFromVaultAsUsdt(
        vault.balanceOf(alice), 0, alice.address, {"from": alice}
    )
    assert interface.IERC20(USDT_TOKEN).balanceOf(alice) == usdt_amount


@pytest.mark.parametrize("option", [0, 1, 2, 3])
def test_claim_as_cvx(
    fn_isolation, alice, bob, charlie, owner, vault, strategy, zaps, option
):
    amount = int(1e21)
    zaps.setSwapOption(option, {"from": owner})
    for i, account in enumerate([alice, bob, charlie]):
        vault.deposit(account, amount, {"from": account})

    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000

    cvxfxs_amount = amount * (1 - withdrawal_penalty)
    fxs_amount = cvxfxs_to_fxs(cvxfxs_amount)
    eth_amount = fxs_to_eth(fxs_amount, option)
    print("\033[95m" + f"Harvested {OPTIONS[option]}: {eth_amount * 1e-18} ETH")

    cvx_amount = interface.ICurveV2Pool(CURVE_CVX_ETH_POOL).get_dy(0, 1, eth_amount)
    vault.approve(zaps, 2**256 - 1, {"from": alice})

    zaps.claimFromVaultAsCvx(
        vault.balanceOf(alice), 0, alice.address, False, {"from": alice}
    )
    assert interface.IERC20(CVX).balanceOf(alice) == cvx_amount


@pytest.mark.parametrize("option", [0, 1, 2, 3])
def test_claim_as_cvx_and_lock(
    fn_isolation, alice, bob, charlie, owner, vault, strategy, zaps, option
):
    amount = int(1e21)
    zaps.setSwapOption(option, {"from": owner})
    for i, account in enumerate([alice, bob, charlie]):
        vault.deposit(account, amount, {"from": account})

    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000

    cvxfxs_amount = amount * (1 - withdrawal_penalty)
    fxs_amount = cvxfxs_to_fxs(cvxfxs_amount)
    eth_amount = fxs_to_eth(fxs_amount, option)
    print("\033[95m" + f"Harvested {OPTIONS[option]}: {eth_amount * 1e-18} ETH")

    cvx_amount = interface.ICurveV2Pool(CURVE_CVX_ETH_POOL).get_dy(0, 1, eth_amount)
    vault.approve(zaps, 2**256 - 1, {"from": alice})

    zaps.claimFromVaultAsCvx(
        vault.balanceOf(alice), 0, alice.address, True, {"from": alice}
    )
    assert interface.ICVXLocker(CONVEX_LOCKER).balances(alice)[0] == cvx_amount


@pytest.mark.parametrize("option", [0, 1, 2, 3])
def test_claim_as_eth(
    fn_isolation, alice, bob, charlie, owner, vault, strategy, zaps, option
):
    amount = int(1e21)
    alice_original_balance = alice.balance()
    zaps.setSwapOption(option, {"from": owner})
    for i, account in enumerate([alice, bob, charlie]):
        vault.deposit(account, amount, {"from": account})

    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000

    cvxfxs_amount = amount * (1 - withdrawal_penalty)
    fxs_amount = cvxfxs_to_fxs(cvxfxs_amount)
    eth_amount = fxs_to_eth(fxs_amount, option)
    print("\033[95m" + f"Harvested {OPTIONS[option]}: {eth_amount * 1e-18} ETH")

    vault.approve(zaps, 2**256 - 1, {"from": alice})

    zaps.claimFromVaultAsEth(vault.balanceOf(alice), 0, alice.address, {"from": alice})
    assert alice.balance() == eth_amount + alice_original_balance


def test_claim_as_fxs(fn_isolation, alice, bob, charlie, owner, vault, strategy, zaps):
    amount = int(1e21)
    for i, account in enumerate([alice, bob, charlie]):
        vault.deposit(account, amount, {"from": account})
    initial_balance = interface.IERC20(FXS).balanceOf(alice)
    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000

    cvxfxs_amount = amount * (1 - withdrawal_penalty)
    fxs_amount = cvxfxs_to_fxs(cvxfxs_amount)

    vault.approve(zaps, 2**256 - 1, {"from": alice})

    zaps.claimFromVaultAsFxs(vault.balanceOf(alice), 0, alice.address, {"from": alice})
    assert interface.IERC20(FXS).balanceOf(alice) == fxs_amount + initial_balance


@pytest.mark.parametrize("option", [0, 1, 2, 3])
def test_claim_as_spell(
    fn_isolation, alice, bob, charlie, owner, vault, strategy, zaps, option
):
    amount = int(1e21)
    zaps.setSwapOption(option, {"from": owner})
    for i, account in enumerate([alice, bob, charlie]):
        vault.deposit(account, amount, {"from": account})

    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000

    cvxfxs_amount = amount * (1 - withdrawal_penalty)
    fxs_amount = cvxfxs_to_fxs(cvxfxs_amount)
    eth_amount = fxs_to_eth(fxs_amount, option)
    print("\033[95m" + f"Harvested {OPTIONS[option]}: {eth_amount * 1e-18} ETH")

    spell_amount = interface.IUniV2Router(SUSHI_ROUTER).getAmountsOut(
        eth_amount, [WETH, SPELL]
    )[-1]
    vault.approve(zaps, 2**256 - 1, {"from": alice})

    zaps.claimFromVaultViaUniV2EthPair(
        amount, 0, SUSHI_ROUTER, SPELL, alice.address, {"from": alice}
    )
    assert interface.IERC20(SPELL).balanceOf(alice) == spell_amount


def test_not_to_zero(alice, vault, strategy, zaps):

    with brownie.reverts("Invalid address!"):
        zaps.claimFromVaultViaUniV2EthPair(
            vault.balanceOf(alice),
            0,
            SUSHI_ROUTER,
            SPELL,
            ADDRESS_ZERO,
            {"from": alice},
        )

    with brownie.reverts("Invalid address!"):
        zaps.claimFromVaultAsEth(
            vault.balanceOf(alice), 0, ADDRESS_ZERO, {"from": alice}
        )

    with brownie.reverts("Invalid address!"):
        zaps.claimFromVaultAsFxs(
            vault.balanceOf(alice), 0, ADDRESS_ZERO, {"from": alice}
        )

    with brownie.reverts("Invalid address!"):
        zaps.claimFromVaultAsCvx(
            vault.balanceOf(alice), 0, ADDRESS_ZERO, False, {"from": alice}
        )

    with brownie.reverts("Invalid address!"):
        zaps.claimFromVaultAsUsdt(
            vault.balanceOf(alice), 0, ADDRESS_ZERO, {"from": alice}
        )
