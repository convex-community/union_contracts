import brownie
import pytest
from brownie import interface, chain
from decimal import Decimal

from ..utils.constants import (
    CVXCRV,
    CONVEX_TRIPOOL_REWARDS,
    TRICRYPTO,
    CURVE_CVXCRV_CRV_POOL,
    CVXCRV_REWARDS,
    CURVE_CRV_ETH_POOL,
    CURVE_CVX_ETH_POOL,
    USDT_TOKEN,
    TRIPOOL,
    CONVEX_LOCKER,
)
from ..utils import cvxcrv_balance, approx
from ..utils.merkle import OrderedMerkleTree


def test_all_claims(
    alice, bob, charlie, dave, vault, owner, merkle_distributor_v2, zaps
):
    amount = int(1e21)
    chain.snapshot()
    claimers = [owner, alice, bob, charlie, dave]
    data = [{"user": claimer.address, "amount": amount} for claimer in claimers]
    tree = OrderedMerkleTree(data)
    merkle_distributor_v2.freeze({"from": owner})
    merkle_distributor_v2.updateMerkleRoot(tree.get_root(), True, {"from": owner})
    merkle_distributor_v2.setApprovals({"from": owner})

    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000

    proofs = tree.get_proof(alice.address)
    crv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(
        1, 0, amount * (1 - withdrawal_penalty)
    )
    eth_amount = interface.ICurveV2Pool(CURVE_CRV_ETH_POOL).get_dy(1, 0, crv_amount)
    usdt_amount = interface.ICurveV2Pool(TRICRYPTO).get_dy(2, 0, eth_amount)
    vault.approve(zaps, 2 ** 256 - 1, {"from": alice})
    zaps.claimFromDistributorAsUsdt(
        proofs["claim"]["index"],
        alice.address,
        amount,
        proofs["proofs"],
        0,
        alice.address,
        {"from": alice},
    )
    assert interface.IERC20(USDT_TOKEN).balanceOf(alice) == usdt_amount

    proofs = tree.get_proof(bob.address)
    crv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(
        1, 0, amount * (1 - withdrawal_penalty)
    )
    eth_amount = interface.ICurveV2Pool(CURVE_CRV_ETH_POOL).get_dy(1, 0, crv_amount)
    usdt_amount = interface.ICurveV2Pool(TRICRYPTO).get_dy(2, 0, eth_amount)
    tricrv_amount = (
        usdt_amount * 1e12 // interface.ITriPool(TRIPOOL).get_virtual_price()
    )
    vault.approve(zaps, 2 ** 256 - 1, {"from": bob})
    zaps.claimFromDistributorAndStakeIn3PoolConvex(
        proofs["claim"]["index"],
        bob.address,
        amount,
        proofs["proofs"],
        0,
        bob.address,
        {"from": bob},
    )
    assert approx(
        interface.IRewards(CONVEX_TRIPOOL_REWARDS).balanceOf(bob) * 1e-18,
        tricrv_amount,
        1,
    )

    proofs = tree.get_proof(charlie.address)
    crv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(
        1, 0, amount * (1 - withdrawal_penalty)
    )
    eth_amount = interface.ICurveV2Pool(CURVE_CRV_ETH_POOL).get_dy(1, 0, crv_amount)
    cvx_amount = interface.ICurveV2Pool(CURVE_CVX_ETH_POOL).get_dy(0, 1, eth_amount)
    vault.approve(zaps, 2 ** 256 - 1, {"from": charlie})
    zaps.claimFromDistributorAsCvxAndLock(
        proofs["claim"]["index"],
        charlie.address,
        amount,
        proofs["proofs"],
        0,
        charlie.address,
        {"from": charlie},
    )
    assert approx(
        interface.ICVXLocker(CONVEX_LOCKER).balances(charlie)[0] * 1e-18,
        cvx_amount * 1e-18,
        1,
    )
    chain.revert()
