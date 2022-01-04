from Crypto.Hash import keccak
from web3 import Web3


def abi_encode(index, account, amount):
    v = Web3.soliditySha3(["uint256", "address", "uint256"], [index, account, amount])
    return bytearray(v)


class OrderedMerkleTree(object):
    def __init__(self, data):
        self.data = sorted(data, key=lambda x: bytearray.fromhex(x["user"][2:]))
        self.claimers = [x["user"] for x in self.data]
        self.amounts = [x["amount"] for x in self.data]
        _unsorted_encoded_data = [
            abi_encode(i, claimer, self.amounts[i])
            for i, claimer in enumerate(self.claimers)
        ]
        _sorted_encoded_data = [
            i for i in sorted(enumerate(_unsorted_encoded_data), key=lambda x: x[1])
        ]
        self.index, self.encoded_data = list(zip(*_sorted_encoded_data))
        self.tree = MerkleTree()
        for encoded_data in self.encoded_data:
            self.tree.add_leaf(encoded_data)
        self.tree.make_tree()

    def get_proofs(self):
        res = {}
        res["root"] = "0x" + self.tree.get_merkle_root()
        res["proofs"] = []
        for i, index in enumerate(self.index):
            original_data = {
                "index": index,
                "user": self.claimers[index],
                "amount": self.amounts[index],
            }
            proofs = [
                "0x" + item for a in self.tree.get_proof(i) for item in list(a.values())
            ]
            res["proofs"].append({"claim": original_data, "proofs": proofs})
        res["proofs"] = sorted(res["proofs"], key=lambda x: x["claim"]["index"])
        return res

    def get_root(self):
        return "0x" + self.tree.get_merkle_root()

    def get_proof(self, claimer):
        all_proofs = self.get_proofs()["proofs"]
        claimer_proof = [
            x for x in all_proofs if x["claim"]["user"].lower() == claimer.lower()
        ]
        if len(claimer_proof) == 0:
            return None
        else:
            return claimer_proof[0]


class Keccak:
    def __init__(self, data):
        self.data = data

    def digest(self):
        return keccak.new(data=self.data, digest_bits=256).digest()

    def hexdigest(self):
        return self.digest().hex()


class MerkleTree(object):
    def __init__(self):
        self.hash_function = Keccak
        self.reset_tree()

    def reset_tree(self):
        self.leaves = list()
        self.levels = None
        self.is_ready = False

    def add_leaf(self, v):
        self.is_ready = False
        self.leaves.append(v)

    def concat(self, a, b):
        a, b = sorted([a, b])
        return a + b

    def get_leaf(self, index):
        return self.leaves[index].hex()

    def get_leaf_count(self):
        return len(self.leaves)

    def get_tree_ready_state(self):
        return self.is_ready

    def _calculate_next_level(self):
        solo_leave = None
        N = len(self.levels[0])  # number of leaves on the level
        if N % 2 == 1:  # if odd number of leaves on the level
            solo_leave = self.levels[0][-1]
            N -= 1

        new_level = []
        for l, r in zip(self.levels[0][0:N:2], self.levels[0][1:N:2]):
            new_level.append(self.hash_function(self.concat(l, r)).digest())
        if solo_leave is not None:
            new_level.append(solo_leave)
        self.levels = [
            new_level,
        ] + self.levels  # prepend new level

    def make_tree(self):
        self.is_ready = False
        if self.get_leaf_count() > 0:
            self.levels = [
                self.leaves,
            ]
            while len(self.levels[0]) > 1:
                self._calculate_next_level()
        self.is_ready = True

    def get_merkle_root(self):
        if self.is_ready:
            if self.levels is not None:
                return self.levels[0][0].hex()
            else:
                return None
        else:
            return None

    def get_proof(self, index):
        if self.levels is None:
            return None
        elif not self.is_ready or index > len(self.leaves) - 1 or index < 0:
            return None
        else:
            proof = []
            for x in range(len(self.levels) - 1, 0, -1):
                level_len = len(self.levels[x])
                if (index == level_len - 1) and (
                    level_len % 2 == 1
                ):  # skip if this is an odd end node
                    index = int(index / 2.0)
                    continue
                is_right_node = index % 2
                sibling_index = index - 1 if is_right_node else index + 1
                sibling_pos = "left" if is_right_node else "right"
                sibling_value = self.levels[x][sibling_index].hex()
                proof.append({sibling_pos: sibling_value})
                index = int(index / 2.0)
            return proof

    def validate_proof(self, proof, target_hash, merkle_root):
        merkle_root = bytearray.fromhex(merkle_root)
        target_hash = bytearray.fromhex(target_hash)
        if len(proof) == 0:
            return target_hash == merkle_root
        else:
            proof_hash = target_hash
            for p in proof:
                try:
                    # the sibling is a left node
                    sibling = bytearray.fromhex(p["left"])
                    proof_hash = self.hash_function(sibling + proof_hash).digest()
                except:
                    # the sibling is a right node
                    sibling = bytearray.fromhex(p["right"])
                    proof_hash = self.hash_function(proof_hash + sibling).digest()
            return proof_hash == merkle_root
