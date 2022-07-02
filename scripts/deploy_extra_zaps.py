from brownie import accounts, interface, ExtraZaps

VAULT = "0x83507cc8C8B67Ed48BADD1F59F684D5d02884C81"
MERKLE_DISTRIBUTOR = "0xA83043Df401346A67eddEb074679B4570b956183"
AIRFORCE_SAFE = "0x9Bc7c6ad7E7Cf3A6fCB58fb21e27752AC1e53f99"
CRV_TOKEN = "0xD533a949740bb3306d119CC777fa900bA034cd52"
CURVE_CVXCRV_CRV_POOL = "0x9D0464996170c6B9e75eED71c68B99dDEDf279e8"


def main():

    deployer = accounts.load("mainnet-deploy")
    zaps = ExtraZaps.deploy(VAULT, MERKLE_DISTRIBUTOR, {"from": deployer})
    zaps.setApprovals({"from": deployer})
    zaps.transferOwnership(AIRFORCE_SAFE, {"from": deployer})

    assert zaps.owner() == AIRFORCE_SAFE
    assert (
        interface.IERC20(CRV_TOKEN).allowance(zaps, CURVE_CVXCRV_CRV_POOL)
        == 2**256 - 1
    )
    ExtraZaps.publish_source(zaps)
