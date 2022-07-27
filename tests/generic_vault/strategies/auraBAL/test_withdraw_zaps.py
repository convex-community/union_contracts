import brownie
import pytest
from brownie import interface
from decimal import Decimal

from ....utils.aurabal import (
    estimate_underlying_received_baleth,
    get_aurabal_to_lptoken_amount,
)
from ....utils.constants import (
    SUSHI_ROUTER,
    WETH,
    SPELL,
    ADDRESS_ZERO,
    BAL_TOKEN,
)


def test_claim_as_eth(fn_isolation, alice, bob, charlie, owner, vault, strategy, zaps):
    amount = int(1e21)
    alice_original_balance = alice.balance()

    for i, account in enumerate([alice, bob, charlie]):
        vault.deposit(account, amount, {"from": account})

    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000
    lp_token_amount = get_aurabal_to_lptoken_amount(
        int(amount * (1 - withdrawal_penalty))
    )
    eth_amount = estimate_underlying_received_baleth(strategy, lp_token_amount, 1)

    vault.approve(zaps, 2**256 - 1, {"from": alice})

    tx = zaps.claimFromVaultAsUnderlying(
        vault.balanceOf(alice), 1, 0, alice.address, False, {"from": alice}
    )
    assert alice.balance() == eth_amount + alice_original_balance


@pytest.mark.parametrize("asset_index", [0, 1])
def test_claim_as_underlying(
    fn_isolation, alice, bob, charlie, owner, vault, strategy, zaps, asset_index
):
    amount = int(1e21)
    for i, account in enumerate([alice, bob, charlie]):
        vault.deposit(account, amount, {"from": account})

    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000
    lp_token_amount = get_aurabal_to_lptoken_amount(
        int(amount * (1 - withdrawal_penalty))
    )
    ul_amount = estimate_underlying_received_baleth(
        strategy, lp_token_amount, asset_index
    )

    asset = [BAL_TOKEN, WETH]
    initial_balance = interface.IERC20(asset[asset_index]).balanceOf(alice)

    vault.approve(zaps, 2**256 - 1, {"from": alice})

    tx = zaps.claimFromVaultAsUnderlying(
        vault.balanceOf(alice), asset_index, 0, alice.address, True, {"from": alice}
    )
    assert (
        interface.IERC20(asset[asset_index]).balanceOf(alice)
        == ul_amount + initial_balance
    )


def test_claim_as_spell(
    fn_isolation, alice, bob, charlie, owner, vault, strategy, zaps
):
    amount = int(1e21)
    for i, account in enumerate([alice, bob, charlie]):
        vault.deposit(account, amount, {"from": account})

    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000
    lp_token_amount = get_aurabal_to_lptoken_amount(
        int(amount * (1 - withdrawal_penalty))
    )
    eth_amount = estimate_underlying_received_baleth(strategy, lp_token_amount, 1)

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
            int(1e18), 0, SUSHI_ROUTER, SPELL, ADDRESS_ZERO, {"from": alice}
        )

    with brownie.reverts("Invalid address!"):
        zaps.claimFromVaultAsUnderlying(
            vault.balanceOf(alice), 1, 0, ADDRESS_ZERO, True, {"from": alice}
        )
