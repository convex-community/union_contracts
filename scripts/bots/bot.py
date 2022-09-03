import requests
import json
from typing import Optional
import os
import time
import eth_abi
from web3 import Web3, HTTPProvider
from eth_account import Account

BAL_VAULT = "0xBA12222222228d8Ba445958a75a0704d566BF2C8"
AURABAL_BAL_ETH_BPT_POOL_ID = (
    "0x3dd0843a028c86e0b760b1a76929d1c5ef93a2dd000200000000000000000249"
)
AURABAL_TOKEN = "0x616e8BfA43F920657B3497DBf40D6b1A02D4608d"
BAL_ETH_POOL_TOKEN = "0x5c6Ee304399DBdB9C8Ef030aB642B10820DB8F56"

ALCHEMY_API_KEY = os.environ["ALCHEMY_API_KEY"]
PROVIDER = f"https://eth-mainnet.alchemyapi.io/v2/{ALCHEMY_API_KEY}"
web3 = Web3(HTTPProvider(PROVIDER))
BOT_ADDRESS = Web3.toChecksumAddress("0x2251AF9804d0A1A04e8e0e7A1FBB83F4D7423f9e")
ACCOUNT = os.environ["HARVESTER_KEY"]


def get_gas_price() -> Optional[int]:
    r = requests.get("https://api.ethgasstation.info/api/fee-estimate")
    gas_price = json.loads(r.content).get("gasPrice", {}).get("standard")
    return gas_price


if __name__ == "__main__":
    account = Account.from_key(ACCOUNT)
    location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    bot_abi = json.load(open(os.path.join(location, "abis/AuraBalBotZap.json"), "r"))
    bal_vault_abi = json.load(open(os.path.join(location, "abis/BalVault.json"), "r"))

    bot = web3.eth.contract(BOT_ADDRESS, abi=bot_abi)
    bal_vault = web3.eth.contract(BAL_VAULT, abi=bal_vault_abi)

    while True:
        try:
            amount = int(1e20)
            swap_step = (
                AURABAL_BAL_ETH_BPT_POOL_ID,
                0,
                1,
                amount,
                eth_abi.encode_abi(["uint256"], [0]),
            )
            assets = [BAL_ETH_POOL_TOKEN, AURABAL_TOKEN]
            funds = (BOT_ADDRESS, False, BOT_ADDRESS, False)
            ratio = (
                bal_vault.functions.queryBatchSwap(0, [swap_step], assets, funds).call()[-1]
                * -1
            )

            gas_price = 8 #get_gas_price()
            lock = ratio > amount
            gas_used = bot.functions.harvest(0, lock).estimate_gas(
                {"from": account.address}
            )
            print(f"GAS PRICE: {gas_price} GAS USED: {gas_used}")
            eth_received = bot.functions.harvest(0, lock).call({"from": account.address})
            gas_cost = gas_used * gas_price * 1e9
            print(f"AuraBAL to ETH20BAL80LP Ratio: {ratio} (Lock: {lock})")
            print(f"Gas price: {gas_price}")
            print(f"Gas used: {gas_used}")
            print(f"Gas cost (ETH): {gas_cost * 1e-18} ({gas_cost})")
            print(f"ETH received: {eth_received * 1e-18} ({eth_received})")
            if (eth_received - gas_cost) > 1e15:
                print("Calling harvest")
                try:
                    nonce = web3.eth.get_transaction_count(account.address)
                    tx = bot.functions.harvest(int(eth_received * 0.9), lock).build_transaction(
                        {"chainId": 1, "nonce": nonce, "from": account.address}
                    )
                    signed = account.sign_transaction(tx)
                    hash = web3.eth.send_raw_transaction(signed.rawTransaction)
                    print("Waiting for approval transaction receipt")
                    receipt = web3.eth.wait_for_transaction_receipt(hash)
                    print("Tx confirmed %s " % receipt)
                except Exception as e:
                    print(f"Error: {e}")
            time.sleep(60)
        except Exception as e:
            print("Error: ", e)
