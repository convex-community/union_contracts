from secrets import token_hex
from types import SimpleNamespace

import pytest
from brownie import UnionZap, accounts, interface, web3

from scripts import deploy_reusd_swapper, propose_reusd_swapper
from scripts.deploy_reusd_swapper import REUSD_TOKEN, UNION_ZAP


def safe_calldata(signature, types=(), values=()):
    return web3.keccak(text=signature)[:4] + web3.codec.encode_abi(types, values)


@pytest.fixture
def prepared_replacement(fn_isolation, monkeypatch):
    monkeypatch.setattr(deploy_reusd_swapper, "chain", SimpleNamespace(id=1))
    monkeypatch.setattr(propose_reusd_swapper, "chain", SimpleNamespace(id=1))
    monkeypatch.setattr(accounts, "load", lambda name: accounts[0])
    swapper = deploy_reusd_swapper.main(publish=False)
    zap = UnionZap.at(UNION_ZAP)
    safe = interface.ISafe(zap.owner())
    owners = web3.codec.decode_abi(
        ["address[]"],
        web3.eth.call({"to": safe.address, "data": safe_calldata("getOwners()")}),
    )[0]
    # Give disposable keys ownership on the local fork, never loading real owner keys.
    signers = [accounts.add("0x" + token_hex(32)), accounts.add("0x" + token_hex(32))]
    safe_account = accounts.at(safe.address, force=True)
    accounts[0].transfer(safe_account, 10**17)
    for previous, old, new in [
        ("0x0000000000000000000000000000000000000001", owners[0], signers[0]),
        (signers[0], owners[1], signers[1]),
    ]:
        safe_account.transfer(
            safe.address,
            0,
            data=safe_calldata(
                "swapOwner(address,address,address)",
                ["address", "address", "address"],
                [str(previous), old, new.address],
            ),
        )

    def load_signer(name):
        assert name == "mainnet-deploy"
        return signers[0]

    monkeypatch.setattr(accounts, "load", load_signer)
    return zap, safe, swapper, signers


@pytest.mark.parametrize(
    "queued,explicit_nonce", [(False, False), (True, False), (False, True)]
)
def test_signed_safe_proposal(
    prepared_replacement, monkeypatch, queued, explicit_nonce
):
    zap, safe, swapper, signers = prepared_replacement
    original_info = zap.tokenInfo(REUSD_TOKEN)
    current_nonce = safe.nonce()
    expected_nonce = current_nonce + (7 if explicit_nonce else 3 if queued else 0)
    monkeypatch.setenv("SAFE_API_KEY", "test-api-key")
    submitted = []

    def get_pending(url, params, headers, timeout):
        assert url.endswith(f"/safes/{safe.address}/multisig-transactions/")
        assert params == {
            "executed": "false",
            "nonce__gte": current_nonce,
            "ordering": "-nonce",
            "limit": 1,
        }
        assert headers == {"Authorization": "Bearer test-api-key"}
        return SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {
                "results": [{"nonce": str(current_nonce + 2)}] if queued else []
            },
        )

    def post_proposal(url, json, headers, timeout):
        assert (
            url
            == f"{propose_reusd_swapper.SAFE_SERVICE}/safes/{safe.address}/multisig-transactions/"
        )
        assert headers == {"Authorization": "Bearer test-api-key"}
        submitted.append(json)
        return SimpleNamespace(ok=True)

    monkeypatch.setattr(propose_reusd_swapper.requests, "get", get_pending)
    monkeypatch.setattr(propose_reusd_swapper.requests, "post", post_proposal)
    nonce = str(expected_nonce) if explicit_nonce else None
    payload = propose_reusd_swapper.main(swapper.address, nonce)
    assert submitted == [payload]
    assert payload["nonce"] == expected_nonce
    assert payload["sender"] == signers[0].address
    assert payload["to"] == zap.address
    assert payload["operation"] == 0
    assert payload["value"] == "0"
    assert payload["contractTransactionHash"].startswith("0x")
    assert payload["signature"].startswith("0x")
    _, decoded = zap.decode_input(payload["data"])
    assert decoded[0] == REUSD_TOKEN
    assert list(decoded[1]) == [swapper.address, swapper.address, original_info[2]]
    # Posting a proposal does not activate it or consume an on-chain nonce.
    assert zap.tokenInfo(REUSD_TOKEN) == original_info
    assert safe.nonce() == current_nonce

    tx_args = [
        payload[name]
        for name in [
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
        ]
    ]
    tx_args[1] = int(tx_args[1])
    safe_hash = safe.getTransactionHash(*tx_args)
    assert web3.toHex(safe_hash) == payload["contractTransactionHash"]
    first_signature = bytes.fromhex(payload["signature"][2:])
    # Validate the submitted owner signature using the real deployed Safe code.
    web3.eth.call(
        {
            "to": safe.address,
            "data": safe_calldata(
                "checkNSignatures(bytes32,bytes,bytes,uint256)",
                ["bytes32", "bytes", "bytes", "uint256"],
                [safe_hash, b"", first_signature, 1],
            ),
        }
    )
    if not queued and not explicit_nonce:
        second_signature = web3.eth.account.signHash(
            safe_hash, private_key=signers[1].private_key
        ).signature
        signatures = b"".join(
            sig
            for _, sig in sorted(
                [
                    (signers[0].address.lower(), first_signature),
                    (signers[1].address.lower(), second_signature),
                ]
            )
        )
        tx_args[2] = bytes.fromhex(tx_args[2][2:])
        accounts[0].transfer(
            safe.address,
            0,
            data=safe_calldata(
                "execTransaction(address,uint256,bytes,uint8,uint256,uint256,uint256,address,address,bytes)",
                [
                    "address",
                    "uint256",
                    "bytes",
                    "uint8",
                    "uint256",
                    "uint256",
                    "uint256",
                    "address",
                    "address",
                    "bytes",
                ],
                tx_args[:-1] + [signatures],
            ),
        )
        assert list(zap.tokenInfo(REUSD_TOKEN)) == [
            swapper.address,
            swapper.address,
            original_info[2],
        ]
        assert safe.nonce() == current_nonce + 1


def test_reject_non_owner(prepared_replacement, monkeypatch):
    _, _, swapper, _ = prepared_replacement
    monkeypatch.setattr(
        accounts, "load", lambda name: accounts.add("0x" + token_hex(32))
    )
    with pytest.raises(ValueError, match="not an owner"):
        propose_reusd_swapper.main(swapper.address)


def test_proposal_service_failure(prepared_replacement, monkeypatch):
    _, safe, swapper, _ = prepared_replacement
    monkeypatch.delenv("SAFE_API_KEY", raising=False)
    monkeypatch.setattr(
        propose_reusd_swapper.requests,
        "post",
        lambda *args, **kwargs: SimpleNamespace(
            ok=False, status_code=401, text="Authentication required"
        ),
    )
    with pytest.raises(RuntimeError, match=r"Safe proposal failed \(401\)"):
        propose_reusd_swapper.main(swapper.address, safe.nonce())
