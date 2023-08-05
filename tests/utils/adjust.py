from brownie import interface
from decimal import Decimal
from requests_cache import CachedSession
import json

from . import eth_to_crv, eth_to_cvx, crv_to_cvxcrv_v2
from .constants import (
    CRV,
    CVX,
    MAX_WEIGHT_1E9,
)
from .cvxfxs import eth_to_fxs

DECIMAL_18 = Decimal(1000000000000000000)
session = CachedSession("test_cache", expire_after=300)


def get_spot_prices(token):
    r = session.get(
        f"https://api.coingecko.com/api/v3/simple/token_price/ethereum?contract_addresses={token}&vs_currencies=ETH"
    )
    data = json.loads(r.content)
    try:
        price = data[token.lower()]["eth"]
    except KeyError:
        print("Failed to get price from Coingecko, trying defillama")
        r = session.get(f"https://coins.llama.fi/prices/current/ethereum:{token}")
        data = json.loads(r.content)
        price = data["coins"][f"ethereum:{token}"]["price"]
    return price


def simulate_adjust(union_contract, lock, weights, option, output_tokens, adjust_order):
    total_eth = union_contract.balance()
    fees = union_contract.platformFee()

    prices = [0] * len(weights)
    amounts = [0] * len(weights)
    output_amounts = [0] * len(weights)
    for order, weight in enumerate(weights):
        if weight > 0:
            output_token = output_tokens[order]
            prices[order] = interface.ICurveV2Pool(
                union_contract.tokenInfo(output_token)[0]
            ).price_oracle()
            amounts[order] = int(
                Decimal(interface.IERC20(output_token).balanceOf(union_contract))
                * Decimal(prices[order])
                / DECIMAL_18
            )
            total_eth += amounts[order]

    fee_amount = int(Decimal(total_eth * fees) / Decimal(MAX_WEIGHT_1E9))
    total_eth = total_eth - fee_amount if (total_eth >= fee_amount) else total_eth

    for order in adjust_order:
        weight = weights[order]
        if weight > 0:
            output_token = union_contract.outputTokens(order)
            desired = int(Decimal(total_eth) * Decimal(weights[order]) / MAX_WEIGHT_1E9)
            sell = amounts[order] > desired
            token_balance = interface.IERC20(output_token).balanceOf(union_contract)

            if sell:
                swappable = (
                    Decimal(amounts[order] - desired)
                    * DECIMAL_18
                    / Decimal(prices[order])
                )
            else:
                swappable = desired - amounts[order]

            if output_token == CRV:
                if sell:
                    output_amount = token_balance - swappable
                else:
                    output_amount = token_balance + eth_to_crv(swappable)
                    if not lock:
                        output_amount = crv_to_cvxcrv_v2(output_amount)
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

            output_amounts[order] = output_amount

    return fee_amount, output_amounts
