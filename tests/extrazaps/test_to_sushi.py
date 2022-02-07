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
    SUSHI_ROUTER,
    SPELL,
    WETH,
    ADDRESS_ZERO,
)
from ..utils import cvxcrv_balance, approx
from ..utils.merkle import OrderedMerkleTree


def test_claim_vault_as_spell(alice, bob, vault, zaps):
    amount = int(1e21)
    chain.snapshot()
    for i, account in enumerate([alice, bob]):
        vault.deposit(account, amount, {"from": account})

    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000
    crv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(
        1, 0, amount * (1 - withdrawal_penalty)
    )
    eth_amount = interface.ICurveV2Pool(CURVE_CRV_ETH_POOL).get_dy(1, 0, crv_amount)
    spell_amount = interface.IUniV2Router(SUSHI_ROUTER).getAmountsOut(
        eth_amount, [WETH, SPELL]
    )[-1]
    vault.approve(zaps, 2 ** 256 - 1, {"from": alice})
    with brownie.reverts():
        zaps.claimFromVaultViaUniV2EthPair(
            amount,
            spell_amount * 2,
            SUSHI_ROUTER,
            SPELL,
            alice.address,
            {"from": alice},
        )
    with brownie.reverts("Invalid address!"):
        zaps.claimFromVaultViaUniV2EthPair(
            amount, amount, SUSHI_ROUTER, SPELL, ADDRESS_ZERO, {"from": alice}
        )
    zaps.claimFromVaultViaUniV2EthPair(
        amount, 0, SUSHI_ROUTER, SPELL, alice.address, {"from": alice}
    )
    assert interface.IERC20(SPELL).balanceOf(alice) == spell_amount
    chain.revert()


def test_claim_distributor_as_spell(
    alice, bob, owner, vault, merkle_distributor_v2, zaps
):
    amount = int(1e21)
    chain.snapshot()
    claimers = [owner, alice, bob]
    data = [{"user": claimer.address, "amount": amount} for claimer in claimers]
    tree = OrderedMerkleTree(data)
    merkle_distributor_v2.freeze({"from": owner})
    merkle_distributor_v2.updateMerkleRoot(tree.get_root(), True, {"from": owner})
    merkle_distributor_v2.setApprovals({"from": owner})
    proofs = tree.get_proof(alice.address)

    withdrawal_penalty = Decimal(vault.withdrawalPenalty()) / 10000
    crv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(
        1, 0, amount * (1 - withdrawal_penalty)
    )
    eth_amount = interface.ICurveV2Pool(CURVE_CRV_ETH_POOL).get_dy(1, 0, crv_amount)
    spell_amount = interface.IUniV2Router(SUSHI_ROUTER).getAmountsOut(
        eth_amount, [WETH, SPELL]
    )[-1]
    vault.approve(zaps, 2 ** 256 - 1, {"from": alice})
    with brownie.reverts():
        zaps.claimFromDistributorViaUniV2EthPair(
            proofs["claim"]["index"],
            alice.address,
            amount,
            proofs["proofs"],
            spell_amount * 2,
            SUSHI_ROUTER,
            SPELL,
            alice.address,
            {"from": alice},
        )
    with brownie.reverts("Invalid address!"):
        zaps.claimFromDistributorViaUniV2EthPair(
            proofs["claim"]["index"],
            alice.address,
            amount,
            proofs["proofs"],
            0,
            SUSHI_ROUTER,
            SPELL,
            ADDRESS_ZERO,
            {"from": alice},
        )
    zaps.claimFromDistributorViaUniV2EthPair(
        proofs["claim"]["index"],
        alice.address,
        amount,
        proofs["proofs"],
        0,
        SUSHI_ROUTER,
        SPELL,
        alice.address,
        {"from": alice},
    )
    assert interface.IERC20(SPELL).balanceOf(alice) == spell_amount
    chain.revert()
