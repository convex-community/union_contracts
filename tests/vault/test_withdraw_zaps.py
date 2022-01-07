import brownie
import pytest
from brownie import interface, chain
from decimal import Decimal

from ..utils.constants import (
    CVXCRV_REWARDS,
    CURVE_CVXCRV_CRV_POOL,
    CURVE_CRV_ETH_POOL,
    CURVE_CVX_ETH_POOL,
    CVXCRV,
    CRV,
    CVX,
    ADDRESS_ZERO,
)
from ..utils import approx, cvxcrv_balance


def test_withdraw_as(alice, bob, charlie, dave, erin, owner, vault):
    chain.snapshot()
    cvxcrv = interface.IERC20(CVXCRV)
    crv = interface.IERC20(CRV)
    cvx = interface.IERC20(CVX)

    balances = []
    vault.setApprovals({"from": owner})
    # ensure none of the test accounts are last to withdraw
    vault.deposit(owner, 1, {"from": owner})

    for account in [alice, bob, charlie, dave, erin]:
        balances.append(cvxcrv_balance(account))
        vault.depositAll(account, {"from": account})

    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000

    # claim as CVX
    crv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(
        1, 0, balances[0] // 2 * (1 - withdrawal_penalty)
    )
    eth_amount = interface.ICurveV2Pool(CURVE_CRV_ETH_POOL).get_dy(1, 0, crv_amount)
    cvx_amount = interface.ICurveV2Pool(CURVE_CVX_ETH_POOL).get_dy(0, 1, eth_amount)
    vault.withdrawAs(alice, balances[0] // 2, 3, {"from": alice})
    assert approx(cvx.balanceOf(alice), cvx_amount, 0.01)

    # claim as cvxCRV
    bob_claimable = vault.balanceOfUnderlying(bob)
    vault.withdrawAs(bob, balances[1] // 2, 0, {"from": bob})
    assert approx(
        cvxcrv.balanceOf(bob), bob_claimable // 2 * (1 - withdrawal_penalty), 1e-5
    )

    # claim as CRV
    charlie_initial_balance = crv.balanceOf(charlie)
    charlie_claimable = vault.balanceOfUnderlying(charlie)
    vault.withdrawAs(charlie, balances[2] // 2, 2, {"from": charlie})
    crv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(
        1, 0, charlie_claimable // 2 * (1 - withdrawal_penalty)
    )
    assert approx(crv.balanceOf(charlie), charlie_initial_balance + crv_amount, 0.01)

    # claim as Eth
    dave_original_balance = dave.balance()
    dave_claimable = vault.balanceOfUnderlying(dave)
    crv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(
        1, 0, dave_claimable // 2 * (1 - withdrawal_penalty)
    )
    eth_amount = interface.ICurveV2Pool(CURVE_CRV_ETH_POOL).get_dy(1, 0, crv_amount)
    vault.withdrawAs(dave, balances[3] // 2, 1, {"from": dave})
    assert approx(dave.balance() - dave_original_balance, eth_amount, 0.01)

    # claim and stake
    erin_claimable = vault.balanceOfUnderlying(erin)
    vault.withdrawAs(erin, balances[4] // 2, 4, {"from": erin})
    assert approx(
        interface.IBasicRewards(CVXCRV_REWARDS).balanceOf(erin.address),
        erin_claimable // 2 * (1 - withdrawal_penalty),
        1e-5,
    )
    interface.IBasicRewards(CVXCRV_REWARDS).withdrawAll(False, {"from": erin})
    assert approx(
        cvxcrv.balanceOf(erin), erin_claimable // 2 * (1 - withdrawal_penalty), 1e-5
    )

    chain.revert()


def test_withdraw_all_as(alice, bob, charlie, dave, erin, owner, vault):
    chain.snapshot()
    cvxcrv = interface.IERC20(CVXCRV)
    crv = interface.IERC20(CRV)
    cvx = interface.IERC20(CVX)

    balances = []
    vault.setApprovals({"from": owner})
    # ensure none of the test accounts are last to withdraw
    vault.deposit(owner, 1, {"from": owner})

    for account in [alice, bob, charlie, dave, erin]:
        balances.append(cvxcrv_balance(account))
        vault.depositAll(account, {"from": account})

    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000

    # claim as CVX
    crv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(
        1, 0, balances[0] * (1 - withdrawal_penalty)
    )
    eth_amount = interface.ICurveV2Pool(CURVE_CRV_ETH_POOL).get_dy(1, 0, crv_amount)
    cvx_amount = interface.ICurveV2Pool(CURVE_CVX_ETH_POOL).get_dy(0, 1, eth_amount)
    vault.withdrawAllAs(alice, 3, {"from": alice})
    assert approx(cvx.balanceOf(alice), cvx_amount, 0.01)

    # claim as cvxCRV
    bob_claimable = vault.balanceOfUnderlying(bob)
    vault.withdrawAllAs(bob, 0, {"from": bob})
    assert approx(cvxcrv.balanceOf(bob), bob_claimable * (1 - withdrawal_penalty), 1e-5)

    # claim as CRV
    charlie_initial_balance = crv.balanceOf(charlie)
    charlie_claimable = vault.balanceOfUnderlying(charlie)
    crv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(
        1, 0, charlie_claimable * (1 - withdrawal_penalty)
    )
    vault.withdrawAllAs(charlie, 2, {"from": charlie})
    assert approx(crv.balanceOf(charlie), charlie_initial_balance + crv_amount, 0.01)

    # claim as Eth
    dave_original_balance = dave.balance()
    dave_claimable = vault.balanceOfUnderlying(dave)
    crv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(
        1, 0, dave_claimable * (1 - withdrawal_penalty)
    )
    eth_amount = interface.ICurveV2Pool(CURVE_CRV_ETH_POOL).get_dy(1, 0, crv_amount)
    vault.withdrawAllAs(dave, 1, {"from": dave})
    assert approx(dave.balance() - dave_original_balance, eth_amount, 0.01)

    # claim and stake
    erin_claimable = vault.balanceOfUnderlying(erin)
    vault.withdrawAllAs(erin, 4, {"from": erin})
    assert approx(
        interface.IBasicRewards(CVXCRV_REWARDS).balanceOf(erin.address),
        erin_claimable * (1 - withdrawal_penalty),
        1e-5,
    )
    interface.IBasicRewards(CVXCRV_REWARDS).withdrawAll(False, {"from": erin})
    assert approx(
        cvxcrv.balanceOf(erin), erin_claimable * (1 - withdrawal_penalty), 1e-5
    )

    chain.revert()


def test_withdraw_as_to_address_zero(alice, owner, vault):
    chain.snapshot()
    vault.setApprovals({"from": owner})
    vault.depositAll(alice, {"from": alice})

    with brownie.reverts("Receiver!"):
        vault.withdrawAs(ADDRESS_ZERO, 1, 3, {"from": alice})
    chain.revert()


def test_withdraw_all_as_to_address_zero(alice, owner, vault):
    chain.snapshot()
    vault.setApprovals({"from": owner})
    vault.depositAll(alice, {"from": alice})

    with brownie.reverts("Receiver!"):
        vault.withdrawAllAs(ADDRESS_ZERO, 3, {"from": alice})
    chain.revert()


def test_withdraw_as_to_address_zero_slippage(alice, owner, vault):
    chain.snapshot()
    vault.setApprovals({"from": owner})
    vault.depositAll(alice, {"from": alice})

    with brownie.reverts("Receiver!"):
        vault.withdrawAs(ADDRESS_ZERO, 1, 3, 0, {"from": alice})
    chain.revert()


def test_withdraw_all_as_to_address_zero_slippage(alice, owner, vault):
    chain.snapshot()
    vault.setApprovals({"from": owner})
    vault.depositAll(alice, {"from": alice})

    with brownie.reverts("Receiver!"):
        vault.withdrawAllAs(ADDRESS_ZERO, 3, 0, {"from": alice})
    chain.revert()
