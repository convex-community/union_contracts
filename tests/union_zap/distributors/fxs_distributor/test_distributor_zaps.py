import brownie

from tests.utils.cvxfxs import estimate_underlying_received, fxs_eth_unistable
from tests.utils.merkle import OrderedMerkleTree
from brownie import interface, chain
from decimal import Decimal
from tests.utils.constants import (
    CLAIM_AMOUNT,
    CVX,
    CVXCRV_REWARDS,
    CURVE_CVX_ETH_POOL,
    CURVE_CVXCRV_CRV_POOL,
    CURVE_CRV_ETH_POOL, CVXFXS, FXS, TRICRYPTO,
)
from tests.utils import approx


def test_distrib_zaps(
    fn_isolation, alice, bob, charlie, dave, erin, owner, distributor_zaps, fxs_distributor, fxs_vault, fxs_zaps
):
    cvxfxs = interface.IERC20(CVXFXS)
    fxs = interface.IERC20(FXS)
    cvx = interface.IERC20(CVX)
    fxs_zaps.setSwapOption(2, {"from": owner})
    claimers = [owner, alice, bob, charlie, dave, erin]
    data = [{"user": claimer.address, "amount": CLAIM_AMOUNT} for claimer in claimers]
    tree = OrderedMerkleTree(data)
    fxs_distributor.freeze({"from": owner})
    fxs_distributor.updateMerkleRoot(tree.get_root(), True, {"from": owner})
    fxs_distributor.setApprovals({"from": owner})
    withdrawal_penalty = Decimal(fxs_vault.withdrawalPenalty()) / 10000

    fxs_amount = estimate_underlying_received(CLAIM_AMOUNT * (1 - withdrawal_penalty), 0)
    cvx_fxs_amount = estimate_underlying_received(CLAIM_AMOUNT * (1 - withdrawal_penalty), 1)
    eth_amount = fxs_eth_unistable(fxs_amount)
    usdt_amount = interface.ICurveV2Pool(TRICRYPTO).get_dy(2, 0, eth_amount)
    cvx_amount = interface.ICurveV2Pool(CURVE_CVX_ETH_POOL).get_dy(0, 1, eth_amount)

    # test claim as underlying fxs
    proofs = tree.get_proof(alice.address)
    alice_initial_balance = fxs.balanceOf(alice)
    fxs_vault.approve(distributor_zaps, 2 ** 256 - 1, {"from": alice})
    tx = distributor_zaps.claimAsUnderlying(
        proofs["claim"]["index"], alice.address, CLAIM_AMOUNT, proofs["proofs"], 0, 0, alice, {"from": alice}
    )
    assert approx(
        fxs.balanceOf(alice),
        alice_initial_balance + fxs_amount,
        1e-5,
    )

    # test claim as underlying cvxfxs
    proofs = tree.get_proof(bob.address)
    bob_initial_balance = cvxfxs.balanceOf(bob)
    fxs_vault.approve(distributor_zaps, 2 ** 256 - 1, {"from": bob})
    tx = distributor_zaps.claimAsUnderlying(
        proofs["claim"]["index"], bob.address, CLAIM_AMOUNT, proofs["proofs"], 1, 0, bob, {"from": bob}
    )
    assert approx(
        cvxfxs.balanceOf(bob),
        bob_initial_balance + cvx_fxs_amount,
        1e-5,
    )
