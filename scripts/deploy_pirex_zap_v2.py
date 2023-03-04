from brownie import (
    accounts,
    interface,
    PCvxZaps,
)

def main():
    deployer = accounts.load("mainnet-deploy")
    ucvx_zaps = PCvxZaps.deploy({"from": deployer}, publish_source=True)
    ucvx_zaps.setApprovals({"from": deployer})
