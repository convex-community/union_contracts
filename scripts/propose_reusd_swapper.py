"""Sign and submit a replacement-swapper activation to the Safe queue."""

import os

import requests
from brownie import ReUsdSwapper, UnionZap, accounts, chain, interface, web3

from scripts.deploy_reusd_swapper import REUSD_TOKEN, UNION_ZAP

SAFE_SERVICE = "https://api.safe.global/tx-service/eth/api/v2"
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def main(swapper_address, nonce=None):
    if chain.id != 1:
        raise ValueError("The reUSD activation script requires Ethereum mainnet")

    zap = UnionZap.at(UNION_ZAP)
    safe = interface.ISafe(zap.owner())
    swapper = ReUsdSwapper.at(swapper_address)
    if swapper.depositor() != zap.address or swapper.owner() != safe.address:
        raise ValueError("The replacement must use this zap and be owned by its Safe")
    if not swapper.useOracle():
        raise ValueError("The replacement must have oracle slippage checks enabled")
    current_info = zap.tokenInfo(REUSD_TOKEN)
    if current_info[0] == swapper.address and current_info[1] == swapper.address:
        raise ValueError("This swapper is already active")

    signer = accounts.load("mainnet-deploy")
    if not safe.isOwner(signer.address):
        raise ValueError("mainnet-deploy is not an owner of the zap's Safe")

    headers = {}
    if os.environ.get("SAFE_API_KEY"):
        headers["Authorization"] = f"Bearer {os.environ['SAFE_API_KEY']}"
    url = f"{SAFE_SERVICE}/safes/{safe.address}/multisig-transactions/"
    current_nonce = safe.nonce()
    if nonce is None:
        response = requests.get(
            url,
            params={
                "executed": "false",
                "nonce__gte": current_nonce,
                "ordering": "-nonce",
                "limit": 1,
            },
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        pending = response.json()["results"]
        nonce = (
            max(current_nonce, int(pending[0]["nonce"]) + 1)
            if pending
            else current_nonce
        )
    else:
        nonce = int(nonce)
    if nonce < current_nonce:
        raise ValueError(
            f"Nonce {nonce} has already been used; current nonce is {current_nonce}"
        )

    data = zap.updateOutputToken.encode_input(
        REUSD_TOKEN, [swapper.address, swapper.address, current_info[2]]
    )
    # Call, zero ETH, no gas refund. Ask the deployed Safe for its version-specific hash.
    tx_args = [zap.address, 0, data, 0, 0, 0, 0, ZERO_ADDRESS, ZERO_ADDRESS, nonce]
    safe_tx_hash = safe.getTransactionHash(*tx_args)
    signature = web3.eth.account.signHash(safe_tx_hash, private_key=signer.private_key)
    payload = dict(
        zip(
            [
                "to",
                "value",
                "data",
                "operation",
                "safeTxGas",
                "baseGas",
                "gasPrice",
                "gasToken",
                "refundReceiver",
                "nonce",
            ],
            tx_args,
        )
    )
    payload.update(
        value="0",
        contractTransactionHash=web3.toHex(safe_tx_hash),
        sender=signer.address,
        signature=signature.signature.hex(),
        origin="gramsci: activate corrected reUSD swapper",
    )
    print(f"Safe: {safe.address}; nonce: {nonce}; replacement: {swapper.address}")
    print(f"Safe transaction hash: {payload['contractTransactionHash']}")
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    if not response.ok:
        raise RuntimeError(
            f"Safe proposal failed ({response.status_code}): {response.text}"
        )
    print(
        "Proposal submitted with your signature. A second owner must approve and execute."
    )
    print(f"https://app.safe.global/transactions/queue?safe=eth:{safe.address}")
    return payload
