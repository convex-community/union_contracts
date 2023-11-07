from web3 import Web3
import json
import os
from tests.utils.airdrop.prisma import PRISMA_CLAIMS
from tests.utils.constants import PRISMA
from tests.utils.merkle import OrderedMerkleTree
from brownie import (
    accounts,
    interface,
    AirdropDistributor
)
from brownie.network.gas.strategies import LinearScalingStrategy
from brownie.network import gas_price

PIREX_MULTISIG = "0x6ED9c171E02De08aaEDF0Fc1D589923D807061D6"


def main():
    gas_strategy = LinearScalingStrategy("20 gwei", "45 gwei", 1.2)
    gas_price(gas_strategy)

    data = [{"user": Web3.toChecksumAddress(k), "amount": v} for k, v in PRISMA_CLAIMS.items()]
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

    location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    with open(os.path.join(location, "proofs.json"), "w") as fp:
        json.dump(final_proofs, fp)

    publish = True
    deployer = accounts.load("mainnet-deploy")
    airdrop = AirdropDistributor.deploy(PRISMA, 8, {"from": deployer}, publish_source=publish)
    airdrop.updateMerkleRoot(tree.get_root(), True, {"from": deployer})
    airdrop.updateAdmin(PIREX_MULTISIG)

    assert airdrop.admin() == PIREX_MULTISIG
