import brownie
import pytest
from brownie import interface, chain
from decimal import Decimal

from ....utils.constants import (
    TRICRYPTO,
    USDT_TOKEN,
    SUSHI_ROUTER,
    WETH,
    SPELL,
    ADDRESS_ZERO, PRISMA,
)
from ....utils.cvxprisma import (
    prisma_to_eth,
    cvxprisma_to_prisma,
)


def test_claim_as_usdt(
    fn_isolation, alice, bob, charlie, owner, vault, strategy, zaps
):
    amount = int(1e21)
    for i, account in enumerate([alice, bob, charlie]):
        vault.deposit(account, amount, {"from": account})

    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000

    cvxprisma_amount = amount * (1 - withdrawal_penalty)
    prisma_amount = cvxprisma_to_prisma(cvxprisma_amount)
    eth_amount = prisma_to_eth(prisma_amount)
    print("\033[95m" + f"Harvested: {eth_amount * 1e-18} ETH")

    usdt_amount = interface.ICurveV2Pool(TRICRYPTO).get_dy(2, 0, eth_amount)
    vault.approve(zaps, 2**256 - 1, {"from": alice})

    tx = zaps.claimFromVaultAsUsdt(
        vault.balanceOf(alice), 0, alice.address, {"from": alice}
    )
    assert interface.IERC20(USDT_TOKEN).balanceOf(alice) == usdt_amount


def test_claim_as_eth(
    fn_isolation, alice, bob, charlie, owner, vault, strategy, zaps
):
    amount = int(1e21)
    alice_original_balance = alice.balance()
    for i, account in enumerate([alice, bob, charlie]):
        vault.deposit(account, amount, {"from": account})

    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000

    cvxprisma_amount = amount * (1 - withdrawal_penalty)
    prisma_amount = cvxprisma_to_prisma(cvxprisma_amount)
    eth_amount = prisma_to_eth(prisma_amount)
    print("\033[95m" + f"Harvested: {eth_amount * 1e-18} ETH")

    vault.approve(zaps, 2**256 - 1, {"from": alice})

    zaps.claimFromVaultAsEth(vault.balanceOf(alice), 0, alice.address, {"from": alice})
    assert alice.balance() == eth_amount + alice_original_balance


def test_claim_as_prisma(fn_isolation, alice, bob, charlie, owner, vault, strategy, zaps):
    amount = int(1e21)
    for i, account in enumerate([alice, bob, charlie]):
        vault.deposit(account, amount, {"from": account})
    initial_balance = interface.IERC20(PRISMA).balanceOf(alice)
    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000

    cvxprisma_amount = amount * (1 - withdrawal_penalty)
    prisma_amount = cvxprisma_to_prisma(cvxprisma_amount)

    vault.approve(zaps, 2**256 - 1, {"from": alice})

    zaps.claimFromVaultAsPrisma(vault.balanceOf(alice), 0, alice.address, {"from": alice})
    assert interface.IERC20(PRISMA).balanceOf(alice) == prisma_amount + initial_balance


def test_claim_as_spell(
    fn_isolation, alice, bob, charlie, owner, vault, strategy, zaps
):
    amount = int(1e21)
    for i, account in enumerate([alice, bob, charlie]):
        vault.deposit(account, amount, {"from": account})

    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000

    cvxprisma_amount = amount * (1 - withdrawal_penalty)
    prisma_amount = cvxprisma_to_prisma(cvxprisma_amount)
    eth_amount = prisma_to_eth(prisma_amount)
    print("\033[95m" + f"Harvested: {eth_amount * 1e-18} ETH")

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
        zaps.claimFromVaultAsPrisma(
            vault.balanceOf(alice), 0, ADDRESS_ZERO, {"from": alice}
        )

    with brownie.reverts("Invalid address!"):
        zaps.claimFromVaultAsUsdt(
            vault.balanceOf(alice), 0, ADDRESS_ZERO, {"from": alice}
        )
