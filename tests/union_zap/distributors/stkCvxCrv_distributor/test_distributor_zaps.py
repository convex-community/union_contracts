import brownie
from tests.utils.merkle import OrderedMerkleTree
from brownie import interface
from tests.utils.constants import (
    CLAIM_AMOUNT,
    CVX,
    TRICRYPTO,
    SUSHI_ROUTER,
    WETH,
    CVXCRV_TOKEN,
    CRV_TOKEN,
    USDT_TOKEN, CURVE_CVXCRV_CRV_POOL_V2, FXS,
)
from tests.utils import approx, get_crv_to_eth_amount, eth_to_cvx


def test_claim_as_cvx(
    fn_isolation,
    alice,
    bob,
    owner,
    distributor_zaps,
    distributor,
    vault,
    vault_zaps,
):
    cvx = interface.IERC20(CVX)
    claimers = [owner, alice, bob]
    data = [{"user": claimer.address, "amount": CLAIM_AMOUNT} for claimer in claimers]
    tree = OrderedMerkleTree(data)
    distributor.freeze({"from": owner})
    distributor.updateMerkleRoot(tree.get_root(), True, {"from": owner})
    distributor.setApprovals({"from": owner})

    withdrawal_penalty = (vault.withdrawalPenalty()) / 10000
    crv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL_V2).get_dy(
        1, 0, CLAIM_AMOUNT * (1 - withdrawal_penalty)
    )
    cvx_amount = eth_to_cvx(get_crv_to_eth_amount(crv_amount))
    # test claim as cvx
    proofs = tree.get_proof(alice.address)
    alice_initial_balance = cvx.balanceOf(alice)
    vault.approve(distributor_zaps, 2 ** 256 - 1, {"from": alice})
    tx = distributor_zaps.claimFromDistributorAsCvx(
        proofs["claim"]["index"],
        alice.address,
        CLAIM_AMOUNT,
        proofs["proofs"],
        0,
        alice,
        False,
        {"from": alice},
    )
    assert approx(
        cvx.balanceOf(alice),
        alice_initial_balance + cvx_amount,
        1e-1,
    )


def test_claim_as_eth(
    fn_isolation,
    alice,
    bob,
    owner,
    distributor_zaps,
        distributor,
        vault,
        vault_zaps,
):

    claimers = [owner, alice, bob]
    data = [{"user": claimer.address, "amount": CLAIM_AMOUNT} for claimer in claimers]
    tree = OrderedMerkleTree(data)
    distributor.freeze({"from": owner})
    distributor.updateMerkleRoot(tree.get_root(), True, {"from": owner})
    distributor.setApprovals({"from": owner})
    withdrawal_penalty = (vault.withdrawalPenalty()) / 10000
    crv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL_V2).get_dy(
        1, 0, CLAIM_AMOUNT * (1 - withdrawal_penalty)
    )
    eth_amount = get_crv_to_eth_amount(crv_amount)
    # test claim as cvx
    proofs = tree.get_proof(alice.address)
    alice_initial_balance = alice.balance()
    vault.approve(distributor_zaps, 2 ** 256 - 1, {"from": alice})
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
        1e-1,
    )


def test_claim_as_crv(
    fn_isolation,
    alice,
    bob,
    owner,
    distributor_zaps,
        distributor,
        vault,
        vault_zaps,
):
    crv = interface.IERC20(CRV_TOKEN)
    claimers = [owner, alice, bob]
    data = [{"user": claimer.address, "amount": CLAIM_AMOUNT} for claimer in claimers]
    tree = OrderedMerkleTree(data)
    distributor.freeze({"from": owner})
    distributor.updateMerkleRoot(tree.get_root(), True, {"from": owner})
    distributor.setApprovals({"from": owner})
    withdrawal_penalty = (vault.withdrawalPenalty()) / 10000
    crv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL_V2).get_dy(
        1, 0, CLAIM_AMOUNT * (1 - withdrawal_penalty)
    )
    # test claim as cvx
    proofs = tree.get_proof(alice.address)
    alice_initial_balance = crv.balanceOf(alice)
    vault.approve(distributor_zaps, 2 ** 256 - 1, {"from": alice})
    tx = distributor_zaps.claimFromDistributorAsCrv(
        proofs["claim"]["index"],
        alice.address,
        CLAIM_AMOUNT,
        proofs["proofs"],
        0,
        alice,
        {"from": alice},
    )
    assert approx(
        crv.balanceOf(alice),
        alice_initial_balance + crv_amount,
        1e-1,
    )


def test_claim_as_cvxcrv(
    fn_isolation,
    alice,
    bob,
    owner,
    distributor_zaps,
        distributor,
        vault,
        vault_zaps,
):
    cvxcrv = interface.IERC20(CVXCRV_TOKEN)
    claimers = [owner, alice, bob]
    data = [{"user": claimer.address, "amount": CLAIM_AMOUNT} for claimer in claimers]
    tree = OrderedMerkleTree(data)
    distributor.freeze({"from": owner})
    distributor.updateMerkleRoot(tree.get_root(), True, {"from": owner})
    distributor.setApprovals({"from": owner})

    withdrawal_penalty = (vault.withdrawalPenalty()) / 10000
    withdraw_amount = CLAIM_AMOUNT * (1 - withdrawal_penalty)

    # test claim as cvx
    proofs = tree.get_proof(alice.address)
    alice_initial_balance = cvxcrv.balanceOf(alice)
    vault.approve(distributor_zaps, 2 ** 256 - 1, {"from": alice})
    tx = distributor_zaps.claimFromDistributorAsUnderlying(
        proofs["claim"]["index"],
        alice.address,
        CLAIM_AMOUNT,
        proofs["proofs"],
        alice,
        {"from": alice},
    )
    assert approx(
        cvxcrv.balanceOf(alice),
        alice_initial_balance + withdraw_amount,
        1e-1,
    )


def test_claim_as_usdt(
    fn_isolation,
    alice,
    bob,
    owner,
    distributor_zaps,
        distributor,
        vault,
        vault_zaps,
):
    usdt = interface.IERC20(USDT_TOKEN)
    claimers = [owner, alice, bob]
    data = [{"user": claimer.address, "amount": CLAIM_AMOUNT} for claimer in claimers]
    tree = OrderedMerkleTree(data)
    distributor.freeze({"from": owner})
    distributor.updateMerkleRoot(tree.get_root(), True, {"from": owner})
    distributor.setApprovals({"from": owner})

    withdrawal_penalty = (vault.withdrawalPenalty()) / 10000
    crv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL_V2).get_dy(
        1, 0, CLAIM_AMOUNT * (1 - withdrawal_penalty)
    )
    eth_amount = get_crv_to_eth_amount(crv_amount)
    usdt_amount = interface.ICurveV2Pool(TRICRYPTO).get_dy(2, 0, eth_amount)

    # test claim as cvx
    proofs = tree.get_proof(alice.address)
    alice_initial_balance = usdt.balanceOf(alice)
    vault.approve(distributor_zaps, 2 ** 256 - 1, {"from": alice})
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
        1e-1,
    )


def test_claim_as_fxs(
    fn_isolation,
    alice,
    bob,
    owner,
    distributor_zaps,
        distributor,
        vault,
        vault_zaps,
):
    fxs = interface.IERC20(FXS)
    claimers = [owner, alice, bob]
    data = [{"user": claimer.address, "amount": CLAIM_AMOUNT} for claimer in claimers]
    tree = OrderedMerkleTree(data)
    distributor.freeze({"from": owner})
    distributor.updateMerkleRoot(tree.get_root(), True, {"from": owner})
    distributor.setApprovals({"from": owner})

    withdrawal_penalty = (vault.withdrawalPenalty()) / 10000
    crv_amount = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL_V2).get_dy(
        1, 0, CLAIM_AMOUNT * (1 - withdrawal_penalty)
    )
    eth_amount = get_crv_to_eth_amount(crv_amount)

    fxs_amount = interface.IUniV2Router(SUSHI_ROUTER).getAmountsOut(
        eth_amount, [WETH, FXS]
    )[-1]

    proofs = tree.get_proof(alice.address)
    alice_initial_balance = fxs.balanceOf(alice)
    vault.approve(distributor_zaps, 2 ** 256 - 1, {"from": alice})
    tx = distributor_zaps.claimFromDistributorViaUniV2EthPair(
        proofs["claim"]["index"],
        alice.address,
        CLAIM_AMOUNT,
        proofs["proofs"],
        0,
        SUSHI_ROUTER,
        FXS,
        alice,
        {"from": alice},
    )
    assert approx(
        fxs.balanceOf(alice),
        alice_initial_balance + fxs_amount,
        1e-1,
    )
