from brownie import interface, chain
import brownie
from tests.utils.constants import PRISMA

GRAMSCI = "0x0b98718264cA14d0A17C145FfE1e4F3c38a39372"


def test_claim(fn_isolation, prisma_claim_tree, airdrop, owner):
    initial_balance = interface.IERC20(PRISMA).balanceOf(GRAMSCI)
    proofs = prisma_claim_tree.get_proof(GRAMSCI)
    airdrop.claim(proofs["claim"]["index"],
                  GRAMSCI,
                  proofs["claim"]["amount"],
                  proofs["proofs"], {"from": owner})
    assert interface.IERC20(PRISMA).balanceOf(GRAMSCI) == initial_balance + proofs["claim"]["amount"]


def test_fail_claim(fn_isolation, prisma_claim_tree, airdrop, owner):
    proofs = prisma_claim_tree.get_proof(GRAMSCI)
    with brownie.reverts():
        airdrop.claim(proofs["claim"]["index"],
                      owner,
                      proofs["claim"]["amount"],
                      proofs["proofs"], {"from": owner})


def test_fail_double_claim(fn_isolation, prisma_claim_tree, airdrop, owner):
    proofs = prisma_claim_tree.get_proof(GRAMSCI)
    airdrop.claim(proofs["claim"]["index"],
                  GRAMSCI,
                  proofs["claim"]["amount"],
                  proofs["proofs"], {"from": owner})

    with brownie.reverts("Drop already claimed."):
        airdrop.claim(proofs["claim"]["index"],
                      GRAMSCI,
                      proofs["claim"]["amount"],
                      proofs["proofs"], {"from": owner})


def test_claim_past_deadline(fn_isolation, prisma_claim_tree, airdrop, owner):
    proofs = prisma_claim_tree.get_proof(GRAMSCI)
    chain.sleep(60 * 60 * 24 * 7 * 10)
    chain.mine(1)
    with brownie.reverts("Claims period has finished"):
        airdrop.claim(proofs["claim"]["index"],
                      owner,
                      proofs["claim"]["amount"],
                      proofs["proofs"], {"from": owner})
