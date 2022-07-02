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
)


@pytest.mark.parametrize("option", [0, 1, 2])
def test_claim_as_usdt(
    fn_isolation, alice, bob, charlie, owner, vault, strategy, zaps, option
):
    amount = int(1e21)
    zaps.setSwapOption(option, {"from": owner})
    for i, account in enumerate([alice, bob, charlie]):
        vault.deposit(account, amount, {"from": account})

    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000

    fxs_amount = estimate_underlying_received(amount * (1 - withdrawal_penalty), 0)
    if option == 0:
        eth_amount = fxs_eth_curve(fxs_amount)
        print(f"Harvested Curve: {eth_amount} ETH")
    elif option == 1:
        eth_amount = fxs_eth_uniswap(fxs_amount)
        print(f"Harvested Uniswap: {eth_amount} ETH")
    elif option == 2:
        eth_amount = fxs_eth_unistable(fxs_amount)
        print(f"Harvested UniStable: {eth_amount} ETH")

    usdt_amount = interface.ICurveV2Pool(TRICRYPTO).get_dy(2, 0, eth_amount)
    vault.approve(zaps, 2**256 - 1, {"from": alice})

    zaps.claimFromVaultAsUsdt(vault.balanceOf(alice), 0, alice.address, {"from": alice})
    assert interface.IERC20(USDT_TOKEN).balanceOf(alice) == usdt_amount


@pytest.mark.parametrize("option", [0, 1, 2])
def test_claim_as_cvx(
    fn_isolation, alice, bob, charlie, owner, vault, strategy, zaps, option
):
    amount = int(1e21)
    zaps.setSwapOption(option, {"from": owner})
    for i, account in enumerate([alice, bob, charlie]):
        vault.deposit(account, amount, {"from": account})

    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000

    fxs_amount = estimate_underlying_received(amount * (1 - withdrawal_penalty), 0)
    if option == 0:
        eth_amount = fxs_eth_curve(fxs_amount)
        print(f"Harvested Curve: {eth_amount} ETH")
    elif option == 1:
        eth_amount = fxs_eth_uniswap(fxs_amount)
        print(f"Harvested Uniswap: {eth_amount} ETH")
    elif option == 2:
        eth_amount = fxs_eth_unistable(fxs_amount)
        print(f"Harvested UniStable: {eth_amount} ETH")

    cvx_amount = interface.ICurveV2Pool(CURVE_CVX_ETH_POOL).get_dy(0, 1, eth_amount)
    vault.approve(zaps, 2**256 - 1, {"from": alice})

    zaps.claimFromVaultAsCvx(
        vault.balanceOf(alice), 0, alice.address, False, {"from": alice}
    )
    assert interface.IERC20(CVX).balanceOf(alice) == cvx_amount


@pytest.mark.parametrize("option", [0, 1, 2])
def test_claim_as_cvx_and_lock(
    fn_isolation, alice, bob, charlie, owner, vault, strategy, zaps, option
):
    amount = int(1e21)
    zaps.setSwapOption(option, {"from": owner})
    for i, account in enumerate([alice, bob, charlie]):
        vault.deposit(account, amount, {"from": account})

    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000

    fxs_amount = estimate_underlying_received(amount * (1 - withdrawal_penalty), 0)
    if option == 0:
        eth_amount = fxs_eth_curve(fxs_amount)
    elif option == 1:
        eth_amount = fxs_eth_uniswap(fxs_amount)
    elif option == 2:
        eth_amount = fxs_eth_unistable(fxs_amount)

    cvx_amount = interface.ICurveV2Pool(CURVE_CVX_ETH_POOL).get_dy(0, 1, eth_amount)
    vault.approve(zaps, 2**256 - 1, {"from": alice})

    zaps.claimFromVaultAsCvx(
        vault.balanceOf(alice), 0, alice.address, True, {"from": alice}
    )
    assert interface.ICVXLocker(CONVEX_LOCKER).balances(alice)[0] == cvx_amount


@pytest.mark.parametrize("option", [0, 1, 2])
def test_claim_as_eth(
    fn_isolation, alice, bob, charlie, owner, vault, strategy, zaps, option
):
    amount = int(1e21)
    alice_original_balance = alice.balance()
    zaps.setSwapOption(option, {"from": owner})
    for i, account in enumerate([alice, bob, charlie]):
        vault.deposit(account, amount, {"from": account})

    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000

    fxs_amount = estimate_underlying_received(amount * (1 - withdrawal_penalty), 0)
    if option == 0:
        eth_amount = fxs_eth_curve(fxs_amount)
        print(f"Harvested Curve: {eth_amount} ETH")
    elif option == 1:
        eth_amount = fxs_eth_uniswap(fxs_amount)
        print(f"Harvested Uniswap: {eth_amount} ETH")
    elif option == 2:
        eth_amount = fxs_eth_unistable(fxs_amount)
        print(f"Harvested UniStable: {eth_amount} ETH")

    vault.approve(zaps, 2**256 - 1, {"from": alice})

    zaps.claimFromVaultAsEth(vault.balanceOf(alice), 0, alice.address, {"from": alice})
    assert alice.balance() == eth_amount + alice_original_balance


@pytest.mark.parametrize("asset_index", [0, 1])
def test_claim_as_underlying(
    fn_isolation, alice, bob, charlie, owner, vault, strategy, zaps, asset_index
):
    amount = int(1e21)
    for i, account in enumerate([alice, bob, charlie]):
        vault.deposit(account, amount, {"from": account})

    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000

    fxs_amount = estimate_underlying_received(
        amount * (1 - withdrawal_penalty), asset_index
    )

    asset = [FXS, CVXFXS]
    initial_balance = interface.IERC20(asset[asset_index]).balanceOf(alice)

    vault.approve(zaps, 2**256 - 1, {"from": alice})

    zaps.claimFromVaultAsUnderlying(
        vault.balanceOf(alice), asset_index, 0, alice.address, {"from": alice}
    )
    assert (
        interface.IERC20(asset[asset_index]).balanceOf(alice)
        == fxs_amount + initial_balance
    )


@pytest.mark.parametrize("option", [0, 1, 2])
def test_claim_as_spell(
    fn_isolation, alice, bob, charlie, owner, vault, strategy, zaps, option
):
    amount = int(1e21)
    zaps.setSwapOption(option, {"from": owner})
    for i, account in enumerate([alice, bob, charlie]):
        vault.deposit(account, amount, {"from": account})

    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000

    fxs_amount = estimate_underlying_received(amount * (1 - withdrawal_penalty), 0)
    if option == 0:
        eth_amount = fxs_eth_curve(fxs_amount)
        print(f"Harvested Curve: {eth_amount} ETH")
    elif option == 1:
        eth_amount = fxs_eth_uniswap(fxs_amount)
        print(f"Harvested Uniswap: {eth_amount} ETH")
    elif option == 2:
        eth_amount = fxs_eth_unistable(fxs_amount)
        print(f"Harvested UniStable: {eth_amount} ETH")

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
        zaps.claimFromVaultAsUnderlying(
            vault.balanceOf(alice), 0, 0, ADDRESS_ZERO, {"from": alice}
        )

    with brownie.reverts("Invalid address!"):
        zaps.claimFromVaultAsCvx(
            vault.balanceOf(alice), 0, ADDRESS_ZERO, False, {"from": alice}
        )

    with brownie.reverts("Invalid address!"):
        zaps.claimFromVaultAsUsdt(
            vault.balanceOf(alice), 0, ADDRESS_ZERO, {"from": alice}
        )
