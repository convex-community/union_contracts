from brownie import accounts, interface, MerkleDistributor, UnionZap

CVXCRV = "0x62B9c7356A2Dc64a1969e19C23e4f579F9810Aa7"
AIRFORCE_SAFE = "0x9Bc7c6ad7E7Cf3A6fCB58fb21e27752AC1e53f99"
ADDRESS_ZERO = "0x0000000000000000000000000000000000000000"
MERKLE_DISTRIBUTOR_V2 = "0xA83043Df401346A67eddEb074679B4570b956183"
CVXCRV_DEPOSIT = "0x8014595F2AB54cD7c604B00E9fb932176fDc86Ae"
CRV_TOKEN = "0xD533a949740bb3306d119CC777fa900bA034cd52"


def main():
    deployer = accounts.load("mainnet-deploy")
    zap = UnionZap.deploy(MERKLE_DISTRIBUTOR_V2, {"from": deployer}, publish_source=True)
    zap.setApprovals({"from": deployer})
    zap.transferOwnership(AIRFORCE_SAFE, {"from": deployer})
    assert zap.owner() == AIRFORCE_SAFE
    assert interface.IERC20(CRV_TOKEN).allowance(zap, CVXCRV_DEPOSIT) == 2 ** 256 - 1
