import brownie

from tests.utils.cvxfxs import (
    get_cvx_to_eth_amount,
)
from tests.utils.merkle import OrderedMerkleTree
from brownie import interface
from tests.utils.constants import (
    CVX,
    TRICRYPTO,
    SPELL,
    SUSHI_ROUTER,
    WETH,
    CVXCRV_TOKEN,
    CRV_TOKEN,
    USDT_TOKEN,
)
from tests.utils import approx, eth_to_crv, crv_to_cvxcrv_v2
from tests.utils.pirex import get_pcvx_to_cvx_via_lpxcvx

CLAIM_AMOUNT = int(1e19)


def test_claim_as_cvx(
    fn_isolation,
    alice,
    bob,
    owner,
    distributor_zaps,
    cvx_distributor,
    cvx_vault,
    cvx_zaps,
):
    cvx = interface.IERC20(CVX)
    claimers = [owner, alice, bob]
    data = [{"user": claimer.address, "amount": CLAIM_AMOUNT} for claimer in claimers]
    tree = OrderedMerkleTree(data)
    cvx_distributor.freeze({"from": owner})
    cvx_distributor.updateMerkleRoot(tree.get_root(), True, {"from": owner})
    cvx_distributor.setApprovals({"from": owner})
    withdraw_amount = cvx_vault.previewRedeem(CLAIM_AMOUNT)
    cvx_amount = get_pcvx_to_cvx_via_lpxcvx(withdraw_amount)

    # test claim as cvx
    proofs = tree.get_proof(alice.address)
    alice_initial_balance = cvx.balanceOf(alice)
    cvx_vault.approve(distributor_zaps, 2**256 - 1, {"from": alice})
    tx = distributor_zaps.claimFromDistributorAsCvx(
        proofs["claim"]["index"],
        alice.address,
        CLAIM_AMOUNT,
        proofs["proofs"],
        1,
        alice,
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
    cvx_distributor,
    cvx_vault,
    cvx_zaps,
):
    cvx = interface.IERC20(CVX)
    claimers = [owner, alice, bob]
    data = [{"user": claimer.address, "amount": CLAIM_AMOUNT} for claimer in claimers]
    tree = OrderedMerkleTree(data)
    cvx_distributor.freeze({"from": owner})
    cvx_distributor.updateMerkleRoot(tree.get_root(), True, {"from": owner})
    cvx_distributor.setApprovals({"from": owner})
    withdraw_amount = cvx_vault.previewRedeem(CLAIM_AMOUNT)
    cvx_amount = get_pcvx_to_cvx_via_lpxcvx(withdraw_amount)
    eth_amount = get_cvx_to_eth_amount(cvx_amount)
    # test claim as cvx
    proofs = tree.get_proof(alice.address)
    alice_initial_balance = alice.balance()
    cvx_vault.approve(distributor_zaps, 2**256 - 1, {"from": alice})
    tx = distributor_zaps.claimFromDistributorAsEth(
        proofs["claim"]["index"],
        alice.address,
        CLAIM_AMOUNT,
        proofs["proofs"],
        1,
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
    cvx_distributor,
    cvx_vault,
    cvx_zaps,
):
    crv = interface.IERC20(CRV_TOKEN)
    claimers = [owner, alice, bob]
    data = [{"user": claimer.address, "amount": CLAIM_AMOUNT} for claimer in claimers]
    tree = OrderedMerkleTree(data)
    cvx_distributor.freeze({"from": owner})
    cvx_distributor.updateMerkleRoot(tree.get_root(), True, {"from": owner})
    cvx_distributor.setApprovals({"from": owner})
    withdraw_amount = cvx_vault.previewRedeem(CLAIM_AMOUNT)
    cvx_amount = get_pcvx_to_cvx_via_lpxcvx(withdraw_amount)
    crv_amount = eth_to_crv(get_cvx_to_eth_amount(cvx_amount))
    # test claim as cvx
    proofs = tree.get_proof(alice.address)
    alice_initial_balance = crv.balanceOf(alice)
    cvx_vault.approve(distributor_zaps, 2**256 - 1, {"from": alice})
    tx = distributor_zaps.claimFromDistributorAsCrv(
        proofs["claim"]["index"],
        alice.address,
        CLAIM_AMOUNT,
        proofs["proofs"],
        1,
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
    cvx_distributor,
    cvx_vault,
    cvx_zaps,
):
    cvxcrv = interface.IERC20(CVXCRV_TOKEN)
    claimers = [owner, alice, bob]
    data = [{"user": claimer.address, "amount": CLAIM_AMOUNT} for claimer in claimers]
    tree = OrderedMerkleTree(data)
    cvx_distributor.freeze({"from": owner})
    cvx_distributor.updateMerkleRoot(tree.get_root(), True, {"from": owner})
    cvx_distributor.setApprovals({"from": owner})
    withdraw_amount = cvx_vault.previewRedeem(CLAIM_AMOUNT)
    cvx_amount = get_pcvx_to_cvx_via_lpxcvx(withdraw_amount)
    cvxcrv_amount = crv_to_cvxcrv_v2(eth_to_crv(get_cvx_to_eth_amount(cvx_amount)))
    # test claim as cvx
    proofs = tree.get_proof(alice.address)
    alice_initial_balance = cvxcrv.balanceOf(alice)
    cvx_vault.approve(distributor_zaps, 2**256 - 1, {"from": alice})
    tx = distributor_zaps.claimFromDistributorAsCvxCrv(
        proofs["claim"]["index"],
        alice.address,
        CLAIM_AMOUNT,
        proofs["proofs"],
        1,
        alice,
        {"from": alice},
    )
    assert approx(
        cvxcrv.balanceOf(alice),
        alice_initial_balance + cvxcrv_amount,
        1e-1,
    )


def test_claim_as_usdt(
    fn_isolation,
    alice,
    bob,
    owner,
    distributor_zaps,
    cvx_distributor,
    cvx_vault,
    cvx_zaps,
):
    usdt = interface.IERC20(USDT_TOKEN)
    claimers = [owner, alice, bob]
    data = [{"user": claimer.address, "amount": CLAIM_AMOUNT} for claimer in claimers]
    tree = OrderedMerkleTree(data)
    cvx_distributor.freeze({"from": owner})
    cvx_distributor.updateMerkleRoot(tree.get_root(), True, {"from": owner})
    cvx_distributor.setApprovals({"from": owner})
    withdraw_amount = cvx_vault.previewRedeem(CLAIM_AMOUNT)
    cvx_amount = get_pcvx_to_cvx_via_lpxcvx(withdraw_amount)
    eth_amount = get_cvx_to_eth_amount(cvx_amount)
    usdt_amount = interface.ICurveV2Pool(TRICRYPTO).get_dy(2, 0, eth_amount)
    # test claim as cvx
    proofs = tree.get_proof(alice.address)
    alice_initial_balance = usdt.balanceOf(alice)
    cvx_vault.approve(distributor_zaps, 2**256 - 1, {"from": alice})
    tx = distributor_zaps.claimFromDistributorAsUsdt(
        proofs["claim"]["index"],
        alice.address,
        CLAIM_AMOUNT,
        proofs["proofs"],
        1,
        alice,
        {"from": alice},
    )
    assert approx(
        usdt.balanceOf(alice),
        alice_initial_balance + usdt_amount,
        1e-1,
    )


def test_claim_as_spell(
    fn_isolation,
    alice,
    bob,
    owner,
    distributor_zaps,
    cvx_distributor,
    cvx_vault,
    cvx_zaps,
):
    spell = interface.IERC20(SPELL)
    claimers = [owner, alice, bob]
    data = [{"user": claimer.address, "amount": CLAIM_AMOUNT} for claimer in claimers]
    tree = OrderedMerkleTree(data)
    cvx_distributor.freeze({"from": owner})
    cvx_distributor.updateMerkleRoot(tree.get_root(), True, {"from": owner})
    cvx_distributor.setApprovals({"from": owner})
    withdraw_amount = cvx_vault.previewRedeem(CLAIM_AMOUNT)
    cvx_amount = get_pcvx_to_cvx_via_lpxcvx(withdraw_amount)
    eth_amount = get_cvx_to_eth_amount(cvx_amount)
    spell_amount = interface.IUniV2Router(SUSHI_ROUTER).getAmountsOut(
        eth_amount, [WETH, SPELL]
    )[-1]
    proofs = tree.get_proof(alice.address)
    alice_initial_balance = spell.balanceOf(alice)
    cvx_vault.approve(distributor_zaps, 2**256 - 1, {"from": alice})
    tx = distributor_zaps.claimFromDistributorViaUniV2EthPair(
        proofs["claim"]["index"],
        alice.address,
        CLAIM_AMOUNT,
        proofs["proofs"],
        1,
        SUSHI_ROUTER,
        SPELL,
        alice,
        {"from": alice},
    )
    assert approx(
        spell.balanceOf(alice),
        alice_initial_balance + spell_amount,
        1e-1,
    )
