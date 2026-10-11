from types import SimpleNamespace

from brownie import UnionZap, accounts, interface

from scripts import deploy_reusd_swapper
from scripts.deploy_reusd_swapper import REUSD_TOKEN, UNION_ZAP, main


def test_deploy_replacement_and_activate(fn_isolation, monkeypatch):
    def load_deployer(name):
        assert name == "mainnet-deploy"
        return accounts[0]

    # A mainnet fork may use a development chain ID.
    monkeypatch.setattr(deploy_reusd_swapper, "chain", SimpleNamespace(id=1))
    monkeypatch.setattr(accounts, "load", load_deployer)
    output = []
    monkeypatch.setattr(deploy_reusd_swapper, "print", output.append, raising=False)
    zap = UnionZap.at(UNION_ZAP)
    original_info = zap.tokenInfo(REUSD_TOKEN)
    owner = zap.owner()
    swapper = main(publish=False)

    assert swapper.depositor() == zap.address
    assert swapper.owner() == owner
    assert swapper.useOracle()
    # Deployment prepares the replacement; activation belongs to the Safe.
    assert zap.tokenInfo(REUSD_TOKEN) == original_info
    for token, spender in [
        (swapper.CRVUSD_TOKEN(), swapper.TRICRV_POOL()),
        (swapper.CRVUSD_TOKEN(), swapper.SCRVUSD_VAULT()),
        (swapper.SCRVUSD_TOKEN(), swapper.REUSD_POOL()),
        (swapper.REUSD_TOKEN(), swapper.REUSD_POOL()),
    ]:
        assert interface.IERC20(token).allowance(swapper, spender) == 2**256 - 1

    params = [swapper.address, swapper.address, original_info[2]]
    calldata = zap.updateOutputToken.encode_input(REUSD_TOKEN, params)
    assert f"Data: {calldata}" in output
    assert f"To: {zap.address}" in output
    assert f"Submit this transaction from the zap owner Safe: {owner}" in output

    # Rehearse the owner-authorized activation on the local mainnet fork.
    owner_account = accounts.at(owner, force=True)
    accounts[0].transfer(owner_account, 10**17)
    owner_account.transfer(zap, 0, data=calldata)
    assert list(zap.tokenInfo(REUSD_TOKEN)) == params
