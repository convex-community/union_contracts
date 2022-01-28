from brownie import accounts, Contract, interface, UnionVault, MerkleDistributorV2, UnionZap

CVXCRV = "0x62B9c7356A2Dc64a1969e19C23e4f579F9810Aa7"
AIRFORCE_SAFE = "0x9Bc7c6ad7E7Cf3A6fCB58fb21e27752AC1e53f99"
ZAP_V2 = "0xd248E64B2d3D00d7f6a21009c3FcC1BD593600c9"
CVXCRV_DEPOSIT = "0x8014595F2AB54cD7c604B00E9fb932176fDc86Ae"
CRV_TOKEN = "0xD533a949740bb3306d119CC777fa900bA034cd52"


def main():
    deployer = accounts.load("mainnet-deploy")
    union_contract = Contract.from_explorer(ZAP_V2)
    vault = UnionVault.deploy({"from": deployer})
    vault.setApprovals({"from": deployer})
    vault.transferOwnership(AIRFORCE_SAFE, {"from": deployer})
    merkle = MerkleDistributorV2.deploy(vault, union_contract, {"from": deployer})

    merkle.setApprovals({"from": deployer})
    merkle.updateAdmin(AIRFORCE_SAFE, {"from": deployer})
    union_contract.updateDistributor(merkle, {"from": AIRFORCE_SAFE})


    assert union_contract.unionDistributor() == merkle
    assert merkle.admin() == AIRFORCE_SAFE
    assert vault.owner() == AIRFORCE_SAFE
    assert interface.IERC20(CRV_TOKEN).allowance(vault, CVXCRV_DEPOSIT) == 2 ** 256 - 1
    assert interface.IERC20(CVXCRV).allowance(merkle, vault) == 2 ** 256 - 1

