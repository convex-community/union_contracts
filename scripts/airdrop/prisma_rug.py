from web3 import Web3
import json
import os
from tests.utils.airdrop.prisma import PRISMA_CLAIMS
from tests.utils.constants import CVXPRISMA
from tests.utils.merkle import OrderedMerkleTree
from brownie import (
    accounts,
    interface,
)

PIREX_MULTISIG = "0x6ED9c171E02De08aaEDF0Fc1D589923D807061D6"
AIRDROP_CONTRACT = "0x8E6d5cf9B9659D4f8e68EE040bF26E728eF1baA4"

def main():
    amount = interface.IERC20(CVXPRISMA).balanceOf(AIRDROP_CONTRACT)

    data = [{"user": PIREX_MULTISIG, "amount": amount}]
    tree = OrderedMerkleTree(data)
    proofs = tree.get_proofs()

    new_proofs = {
        proof['claim']['user']: {
            'index': proof['claim']['index'],
            'amount': f"0x{(proof['claim']['amount']):x}",
            'proof': proof['proofs']
        }
        for proof in proofs['proofs']
    }
    final_proofs = {
        'id': 'cvxprisma',
        'merkleRoot': proofs['root'],
        'proofs': new_proofs
    }
    print("PROOFS:")
    print(final_proofs)
    print("MERKLE ROOT:")
    print(tree.get_root())
