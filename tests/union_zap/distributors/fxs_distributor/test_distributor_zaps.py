import brownie

from tests.utils.cvxfxs import estimate_underlying_received, fxs_eth_unistable
from tests.utils.merkle import OrderedMerkleTree
from brownie import interface, chain
from decimal import Decimal
from tests.utils.constants import (
    CLAIM_AMOUNT,
    CVX, CURVE_CVX_ETH_POOL, CVXFXS, FXS, TRICRYPTO, USDT, CONVEX_LOCKER, SPELL, SUSHI_ROUTER, WETH,
)
from tests.utils import approx


def test_claim_as_underlying(
    fn_isolation, alice, bob, owner, distributor_zaps, fxs_distributor, fxs_vault, fxs_zaps
):
    cvxfxs = interface.IERC20(CVXFXS)
    fxs = interface.IERC20(FXS)
    fxs_zaps.setSwapOption(2, {"from": owner})
    claimers = [owner, alice, bob]
    data = [{"user": claimer.address, "amount": CLAIM_AMOUNT} for claimer in claimers]
    tree = OrderedMerkleTree(data)
    fxs_distributor.freeze({"from": owner})
    fxs_distributor.updateMerkleRoot(tree.get_root(), True, {"from": owner})
    fxs_distributor.setApprovals({"from": owner})
    withdrawal_penalty = Decimal(fxs_vault.withdrawalPenalty()) / 10000

    fxs_amount = estimate_underlying_received(CLAIM_AMOUNT * (1 - withdrawal_penalty), 0)
    cvx_fxs_amount = estimate_underlying_received(CLAIM_AMOUNT * (1 - withdrawal_penalty), 1)

    # test claim as underlying fxs
    proofs = tree.get_proof(alice.address)
    alice_initial_balance = fxs.balanceOf(alice)
    fxs_vault.approve(distributor_zaps, 2 ** 256 - 1, {"from": alice})
    tx = distributor_zaps.claimFromDistributorAsUnderlying(
        proofs["claim"]["index"], alice.address, CLAIM_AMOUNT, proofs["proofs"], 0, 0, alice, {"from": alice}
    )
    assert approx(
        fxs.balanceOf(alice),
        alice_initial_balance + fxs_amount,
        1e-3,
    )

    # test claim as underlying cvxfxs
    proofs = tree.get_proof(bob.address)
    bob_initial_balance = cvxfxs.balanceOf(bob)
    fxs_vault.approve(distributor_zaps, 2 ** 256 - 1, {"from": bob})
    tx = distributor_zaps.claimFromDistributorAsUnderlying(
        proofs["claim"]["index"], bob.address, CLAIM_AMOUNT, proofs["proofs"], 1, 0, bob, {"from": bob}
    )
    assert approx(
        cvxfxs.balanceOf(bob),
        bob_initial_balance + cvx_fxs_amount,
        1e-3,
    )


def test_claim_as_eth(
    fn_isolation, alice, bob, owner, distributor_zaps, fxs_distributor, fxs_vault, fxs_zaps
):
    fxs_zaps.setSwapOption(2, {"from": owner})
    claimers = [owner, alice, bob]
    data = [{"user": claimer.address, "amount": CLAIM_AMOUNT} for claimer in claimers]
    tree = OrderedMerkleTree(data)
    fxs_distributor.freeze({"from": owner})
    fxs_distributor.updateMerkleRoot(tree.get_root(), True, {"from": owner})
    fxs_distributor.setApprovals({"from": owner})
    withdrawal_penalty = Decimal(fxs_vault.withdrawalPenalty()) / 10000

    fxs_amount = estimate_underlying_received(CLAIM_AMOUNT * (1 - withdrawal_penalty), 0)
    eth_amount = fxs_eth_unistable(fxs_amount)

    # test claim as eth
    proofs = tree.get_proof(alice.address)
    alice_initial_balance = alice.balance()
    fxs_vault.approve(distributor_zaps, 2 ** 256 - 1, {"from": alice})
    tx = distributor_zaps.claimFromDistributorAsEth(
        proofs["claim"]["index"], alice.address, CLAIM_AMOUNT, proofs["proofs"], 0, alice, {"from": alice}
    )
    assert approx(
        alice.balance(),
        alice_initial_balance + eth_amount,
        1e-3,
    )


def test_claim_as_usdt(
    fn_isolation, alice, bob, owner, distributor_zaps, fxs_distributor, fxs_vault, fxs_zaps
):
    usdt = interface.IERC20(USDT)
    fxs_zaps.setSwapOption(2, {"from": owner})
    claimers = [owner, alice, bob]
    data = [{"user": claimer.address, "amount": CLAIM_AMOUNT} for claimer in claimers]
    tree = OrderedMerkleTree(data)
    fxs_distributor.freeze({"from": owner})
    fxs_distributor.updateMerkleRoot(tree.get_root(), True, {"from": owner})
    fxs_distributor.setApprovals({"from": owner})
    withdrawal_penalty = Decimal(fxs_vault.withdrawalPenalty()) / 10000

    fxs_amount = estimate_underlying_received(CLAIM_AMOUNT * (1 - withdrawal_penalty), 0)
    eth_amount = fxs_eth_unistable(fxs_amount)
    usdt_amount = interface.ICurveV2Pool(TRICRYPTO).get_dy(2, 0, eth_amount)

    # test claim as usdt
    proofs = tree.get_proof(alice.address)
    alice_initial_balance = usdt.balanceOf(alice)
    fxs_vault.approve(distributor_zaps, 2 ** 256 - 1, {"from": alice})
    tx = distributor_zaps.claimFromDistributorAsUsdt(
        proofs["claim"]["index"], alice.address, CLAIM_AMOUNT, proofs["proofs"], 0, alice, {"from": alice}
    )
    assert approx(
        usdt.balanceOf(alice),
        alice_initial_balance + usdt_amount,
        1e-3,
    )


def test_claim_as_spell(
    fn_isolation, alice, bob, owner, distributor_zaps, fxs_distributor, fxs_vault, fxs_zaps
):
    spell = interface.IERC20(SPELL)
    fxs_zaps.setSwapOption(2, {"from": owner})
    claimers = [owner, alice, bob]
    data = [{"user": claimer.address, "amount": CLAIM_AMOUNT} for claimer in claimers]
    tree = OrderedMerkleTree(data)
    fxs_distributor.freeze({"from": owner})
    fxs_distributor.updateMerkleRoot(tree.get_root(), True, {"from": owner})
    fxs_distributor.setApprovals({"from": owner})
    withdrawal_penalty = Decimal(fxs_vault.withdrawalPenalty()) / 10000

    fxs_amount = estimate_underlying_received(CLAIM_AMOUNT * (1 - withdrawal_penalty), 0)
    eth_amount = fxs_eth_unistable(fxs_amount)
    spell_amount = interface.IUniV2Router(SUSHI_ROUTER).getAmountsOut(
        eth_amount, [WETH, SPELL]
    )[-1]
    # test claim as spell
    proofs = tree.get_proof(alice.address)
    alice_initial_balance = spell.balanceOf(alice)
    fxs_vault.approve(distributor_zaps, 2 ** 256 - 1, {"from": alice})
    tx = distributor_zaps.claimFromDistributorViaUniV2EthPair(
        proofs["claim"]["index"], alice.address, CLAIM_AMOUNT, proofs["proofs"], 0, SUSHI_ROUTER, SPELL, alice, {"from": alice}
    )
    assert approx(
        spell.balanceOf(alice),
        alice_initial_balance + spell_amount,
        1e-3,
    )


def test_claim_as_cvx_and_lock(
    fn_isolation, alice, bob, owner, distributor_zaps, fxs_distributor, fxs_vault, fxs_zaps
):
    cvx = interface.IERC20(CVX)
    fxs_zaps.setSwapOption(2, {"from": owner})
    claimers = [owner, alice, bob]
    data = [{"user": claimer.address, "amount": CLAIM_AMOUNT} for claimer in claimers]
    tree = OrderedMerkleTree(data)
    fxs_distributor.freeze({"from": owner})
    fxs_distributor.updateMerkleRoot(tree.get_root(), True, {"from": owner})
    fxs_distributor.setApprovals({"from": owner})
    withdrawal_penalty = Decimal(fxs_vault.withdrawalPenalty()) / 10000

    fxs_amount = estimate_underlying_received(CLAIM_AMOUNT * (1 - withdrawal_penalty), 0)
    eth_amount = fxs_eth_unistable(fxs_amount)
    cvx_amount = interface.ICurveV2Pool(CURVE_CVX_ETH_POOL).get_dy(0, 1, eth_amount)

    # test claim as cvx
    proofs = tree.get_proof(alice.address)
    alice_initial_balance = cvx.balanceOf(alice)
    fxs_vault.approve(distributor_zaps, 2 ** 256 - 1, {"from": alice})
    tx = distributor_zaps.claimFromDistributorAsCvx(
        proofs["claim"]["index"], alice.address, CLAIM_AMOUNT, proofs["proofs"], 0, alice, False, {"from": alice}
    )
    assert approx(
        cvx.balanceOf(alice),
        alice_initial_balance + cvx_amount,
        1e-3,
    )

    # test claim as cvx and lock
    proofs = tree.get_proof(bob.address)
    bob_initial_balance = cvx.balanceOf(bob)
    fxs_vault.approve(distributor_zaps, 2 ** 256 - 1, {"from": bob})
    tx = distributor_zaps.claimFromDistributorAsCvx(
        proofs["claim"]["index"], bob.address, CLAIM_AMOUNT, proofs["proofs"], 0, bob, True, {"from": bob}
    )
    assert approx(
        interface.ICVXLocker(CONVEX_LOCKER).balances(bob)[0],
        bob_initial_balance + cvx_amount,
        1e-3,
    )
