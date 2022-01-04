from brownie import accounts, MerkleDistributor, UnionZap

CVXCRV = "0x62B9c7356A2Dc64a1969e19C23e4f579F9810Aa7"
AIRFORCE_SAFE = "0x9Bc7c6ad7E7Cf3A6fCB58fb21e27752AC1e53f99"
ADDRESS_ZERO = "0x0000000000000000000000000000000000000000"


def main():
    deployer = accounts.load("mainnet-deploy")
    zap = UnionZap.deploy(ADDRESS_ZERO, {"from": deployer}, publish_source=True)
    merkle = MerkleDistributor.deploy(CVXCRV, zap, "0x0", {"from": deployer})
    zap.updateDistributor(merkle, {"from": deployer}, publish_source=True)
    zap.transferOwnership(AIRFORCE_SAFE, {"from": deployer})
    merkle.updateAdmin(AIRFORCE_SAFE, {"from": deployer})

    assert merkle.admin() == AIRFORCE_SAFE
    assert merkle.frozen() == True
    assert merkle.token() == CVXCRV
    assert zap.owner() == AIRFORCE_SAFE
