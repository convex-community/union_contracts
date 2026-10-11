from brownie import ReUsdSwapper, UnionZap, accounts, chain

UNION_ZAP = "0xD52Ca71AAfa4d2590aac1E35e3005242dd31e5eD"
REUSD_TOKEN = "0x57aB1E0003F623289CD798B1824Be09a793e4Bec"


def main(publish=True):
    if chain.id != 1:
        raise ValueError("The reUSD replacement script requires Ethereum mainnet")

    zap = UnionZap.at(UNION_ZAP)
    owner = zap.owner()
    distributor = zap.tokenInfo(REUSD_TOKEN)[2]
    deployer = accounts.load("mainnet-deploy")

    swapper = ReUsdSwapper.deploy(zap, {"from": deployer})
    swapper.setApprovals({"from": deployer})
    swapper.transferOwnership(owner, {"from": deployer})

    assert swapper.depositor() == zap.address
    assert swapper.owner() == owner
    assert swapper.useOracle()

    calldata = zap.updateOutputToken.encode_input(
        REUSD_TOKEN, [swapper.address, swapper.address, distributor]
    )
    print(f"Replacement swapper: {swapper.address}")
    print(f"Submit this transaction from the zap owner Safe: {owner}")
    print(f"To: {zap.address}")
    print("Value: 0")
    print(f"Data: {calldata}")
    print(f"Existing distributor: {distributor}")

    # Print the activation call before verification in case the explorer is unavailable.
    if publish:
        ReUsdSwapper.publish_source(swapper)

    return swapper
