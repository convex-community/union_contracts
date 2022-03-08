import brownie
import pytest
from brownie import interface, chain
from decimal import Decimal

from ....utils.constants import (
    TRICRYPTO,
    USDT_TOKEN,
)
from ....utils.cvxfxs import estimate_underlying_received, fxs_eth_curve, fxs_eth_uniswap, fxs_eth_unistable


@pytest.mark.parametrize("option", [0, 1, 2])
def test_claim_as_usdt(fn_isolation, alice, bob, charlie, owner, vault, strategy, zaps, option):
    amount = int(1e21)
    zaps.setSwapOption(option, {"from": owner})
    for i, account in enumerate([alice, bob, charlie]):
        vault.deposit(account, amount, {"from": account})

    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000

    fxs_amount = estimate_underlying_received(amount * (1 - withdrawal_penalty), 0)
    if option == 0:
        eth_amount = fxs_eth_curve(fxs_amount)
        print(f"Harvested Curve: {eth_amount} FXS")
    elif option == 1:
        eth_amount = fxs_eth_uniswap(fxs_amount)
        print(f"Harvested Uniswap: {eth_amount} FXS")
    elif option == 2:
        eth_amount = fxs_eth_unistable(fxs_amount)
        print(f"Harvested UniStable: {eth_amount} FXS")

    usdt_amount = interface.ICurveV2Pool(TRICRYPTO).get_dy(2, 0, eth_amount)
    vault.approve(zaps, 2 ** 256 - 1, {"from": alice})

    zaps.claimFromVaultAsUsdt(vault.balanceOf(alice), 0, alice.address, {"from": alice})
    assert interface.IERC20(USDT_TOKEN).balanceOf(alice) == usdt_amount





def test_not_to_zero(alice, vault, strategy, zaps):

    pass
    """
    with brownie.reverts("Invalid address!"):
        zaps.claimFromVaultAsCvxAndLock(
            vault.balanceOf(alice), 0, ADDRESS_ZERO, {"from": alice}
        )
"""