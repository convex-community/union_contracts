import brownie

from tests.utils.cvxprisma import (
    cvxprisma_to_prisma,
    prisma_to_eth,
)
from tests.utils.merkle import OrderedMerkleTree
from brownie import interface, chain
from decimal import Decimal
from tests.utils.constants import (
    CLAIM_AMOUNT,
    CVXPRISMA,
    PRISMA,
    TRICRYPTO,
    USDT,
    SPELL,
    SUSHI_ROUTER,
    WETH,
)
from tests.utils import approx


def test_claim_as_underlying(
    fn_isolation,
    alice,
    bob,
    owner,
    distributor_zaps,
    prisma_distributor,
    prisma_vault,
    prisma_zaps,
):
    cvxprisma = interface.IERC20(CVXPRISMA)
    prisma = interface.IERC20(PRISMA)
    claimers = [owner, alice, bob]
    data = [{"user": claimer.address, "amount": CLAIM_AMOUNT} for claimer in claimers]
    tree = OrderedMerkleTree(data)
    prisma_distributor.freeze({"from": owner})
    prisma_distributor.updateMerkleRoot(tree.get_root(), True, {"from": owner})
    prisma_distributor.setApprovals({"from": owner})
    withdrawal_penalty = Decimal(prisma_vault.withdrawalPenalty()) / 10000

    prisma_amount = cvxprisma_to_prisma(CLAIM_AMOUNT * (1 - withdrawal_penalty))
    cvx_prisma_amount = CLAIM_AMOUNT * (1 - withdrawal_penalty)

    # test claim as underlying prisma
    proofs = tree.get_proof(alice.address)
    alice_initial_balance = prisma.balanceOf(alice)
    prisma_vault.approve(distributor_zaps, 2**256 - 1, {"from": alice})
    tx = distributor_zaps.claimFromDistributorAsPrisma(
        proofs["claim"]["index"],
        alice.address,
        CLAIM_AMOUNT,
        proofs["proofs"],
        0,
        alice,
        {"from": alice},
    )
    assert approx(
        prisma.balanceOf(alice),
        alice_initial_balance + prisma_amount,
        1e-3,
    )

    # test claim as underlying cvxprisma
    proofs = tree.get_proof(bob.address)
    bob_initial_balance = cvxprisma.balanceOf(bob)
    prisma_vault.approve(distributor_zaps, 2**256 - 1, {"from": bob})
    tx = distributor_zaps.claimFromDistributorAsUnderlying(
        proofs["claim"]["index"],
        bob.address,
        CLAIM_AMOUNT,
        proofs["proofs"],
        bob,
        {"from": bob},
    )
    assert approx(
        cvxprisma.balanceOf(bob),
        bob_initial_balance + cvx_prisma_amount,
        1e-3,
    )


def test_claim_as_eth(
    fn_isolation,
    alice,
    bob,
    owner,
    distributor_zaps,
    prisma_distributor,
    prisma_vault,
    prisma_zaps,
):
    claimers = [owner, alice, bob]
    data = [{"user": claimer.address, "amount": CLAIM_AMOUNT} for claimer in claimers]
    tree = OrderedMerkleTree(data)
    prisma_distributor.freeze({"from": owner})
    prisma_distributor.updateMerkleRoot(tree.get_root(), True, {"from": owner})
    prisma_distributor.setApprovals({"from": owner})
    withdrawal_penalty = Decimal(prisma_vault.withdrawalPenalty()) / 10000

    prisma_amount = cvxprisma_to_prisma(CLAIM_AMOUNT * (1 - withdrawal_penalty))
    eth_amount = prisma_to_eth(prisma_amount)

    # test claim as eth
    proofs = tree.get_proof(alice.address)
    alice_initial_balance = alice.balance()
    prisma_vault.approve(distributor_zaps, 2**256 - 1, {"from": alice})
    tx = distributor_zaps.claimFromDistributorAsEth(
        proofs["claim"]["index"],
        alice.address,
        CLAIM_AMOUNT,
        proofs["proofs"],
        0,
        alice,
        {"from": alice},
    )
    assert approx(
        alice.balance(),
        alice_initial_balance + eth_amount,
        1e-3,
    )


def test_claim_as_usdt(
    fn_isolation,
    alice,
    bob,
    owner,
    distributor_zaps,
    prisma_distributor,
    prisma_vault,
    prisma_zaps,
):
    usdt = interface.IERC20(USDT)
    claimers = [owner, alice, bob]
    data = [{"user": claimer.address, "amount": CLAIM_AMOUNT} for claimer in claimers]
    tree = OrderedMerkleTree(data)
    prisma_distributor.freeze({"from": owner})
    prisma_distributor.updateMerkleRoot(tree.get_root(), True, {"from": owner})
    prisma_distributor.setApprovals({"from": owner})
    withdrawal_penalty = Decimal(prisma_vault.withdrawalPenalty()) / 10000

    prisma_amount = cvxprisma_to_prisma(CLAIM_AMOUNT * (1 - withdrawal_penalty))
    eth_amount = prisma_to_eth(prisma_amount)
    usdt_amount = interface.ICurveV2Pool(TRICRYPTO).get_dy(2, 0, eth_amount)

    # test claim as usdt
    proofs = tree.get_proof(alice.address)
    alice_initial_balance = usdt.balanceOf(alice)
    prisma_vault.approve(distributor_zaps, 2**256 - 1, {"from": alice})
    tx = distributor_zaps.claimFromDistributorAsUsdt(
        proofs["claim"]["index"],
        alice.address,
        CLAIM_AMOUNT,
        proofs["proofs"],
        0,
        alice,
        {"from": alice},
    )
    assert approx(
        usdt.balanceOf(alice),
        alice_initial_balance + usdt_amount,
        1e-3,
    )


def test_claim_as_spell(
    fn_isolation,
    alice,
    bob,
    owner,
    distributor_zaps,
    prisma_distributor,
    prisma_vault,
    prisma_zaps,
):
    spell = interface.IERC20(SPELL)
    claimers = [owner, alice, bob]
    data = [{"user": claimer.address, "amount": CLAIM_AMOUNT} for claimer in claimers]
    tree = OrderedMerkleTree(data)
    prisma_distributor.freeze({"from": owner})
    prisma_distributor.updateMerkleRoot(tree.get_root(), True, {"from": owner})
    prisma_distributor.setApprovals({"from": owner})
    withdrawal_penalty = Decimal(prisma_vault.withdrawalPenalty()) / 10000

    prisma_amount = cvxprisma_to_prisma(CLAIM_AMOUNT * (1 - withdrawal_penalty))
    eth_amount = prisma_to_eth(prisma_amount)
    spell_amount = interface.IUniV2Router(SUSHI_ROUTER).getAmountsOut(
        eth_amount, [WETH, SPELL]
    )[-1]
    # test claim as spell
    proofs = tree.get_proof(alice.address)
    alice_initial_balance = spell.balanceOf(alice)
    prisma_vault.approve(distributor_zaps, 2**256 - 1, {"from": alice})
    tx = distributor_zaps.claimFromDistributorViaUniV2EthPair(
        proofs["claim"]["index"],
        alice.address,
        CLAIM_AMOUNT,
        proofs["proofs"],
        0,
        SUSHI_ROUTER,
        SPELL,
        alice,
        {"from": alice},
    )
    assert approx(
        spell.balanceOf(alice),
        alice_initial_balance + spell_amount,
        1e-3,
    )
