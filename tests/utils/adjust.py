from brownie import interface
from decimal import Decimal
from requests_cache import CachedSession
import requests
import json

from . import eth_to_crv, eth_to_cvx, crv_to_cvxcrv
from .constants import (
    CRV,
    CVX,
    MAX_WEIGHT_1E9,
)
from .cvxfxs import eth_to_fxs

DECIMAL_18 = Decimal(1000000000000000000)
session = CachedSession("test_cache", expire_after=300)


def get_spot_prices(token):
    r = requests.get(
        f"https://api.coingecko.com/api/v3/simple/token_price/ethereum?contract_addresses={token}&vs_currencies=ETH"
    )
    data = json.loads(r.content)
    return data[token.lower()]["eth"]


def simulate_adjust(union_contract, lock, weights, option, output_tokens):
    total_eth = union_contract.balance()
    prices = [0] * len(weights)
    amounts = [0] * len(weights)
    output_amounts = [0] * len(weights)
    for i, weight in enumerate(weights):
        if weight > 0:
            output_token = output_tokens[i]
            prices[i] = interface.ICurveV2Pool(
                union_contract.tokenInfo(output_token)[0]
            ).price_oracle()
            amounts[i] = int(
                Decimal(interface.IERC20(output_token).balanceOf(union_contract))
                * Decimal(prices[i])
                / DECIMAL_18
            )
            total_eth += amounts[i]

    for i, weight in enumerate(weights):
        if weight > 0:
            output_token = union_contract.outputTokens(i)
            desired = int(Decimal(total_eth) * Decimal(weights[i]) / MAX_WEIGHT_1E9)
            sell = amounts[i] > desired
            token_balance = interface.IERC20(output_token).balanceOf(union_contract)

            if sell:
                swappable = (
                    Decimal(amounts[i] - desired) * DECIMAL_18 / Decimal(prices[i])
                )
            else:
                swappable = desired - amounts[i]

            if output_token == CRV:
                if sell:
                    output_amount = token_balance - swappable
                else:
                    output_amount = token_balance + eth_to_crv(swappable)
                    if not lock:
                        output_amount = crv_to_cvxcrv(output_amount)
            elif output_token == CVX:
                if sell:
                    output_amount = token_balance - swappable
                else:
                    output_amount = token_balance + eth_to_cvx(swappable)
            else:
                if sell:
                    output_amount = token_balance - swappable
                else:
                    output_amount = token_balance + eth_to_fxs(swappable, option)

            output_amounts[i] = output_amount

    return output_amounts
