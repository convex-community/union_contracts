from brownie import interface

from tests.utils import get_crv_to_eth_amount, cvxcrv_to_crv
from tests.utils.constants import (
    CURVE_CVX_PCVX_POOL,
    CURVE_CVX_ETH_POOL,
    CLAIM_AMOUNT,
    UNI_ROUTER,
    SUSHI_ROUTER,
    WETH,
    UNI_QUOTER,
    CURVE_CONTRACT_REGISTRY,
    CRV,
    CVXCRV,
    CVX,
)


def get_cvx_to_pxcvx(amount):
    swap_amount = interface.ICurveV2Pool(CURVE_CVX_PCVX_POOL).get_dy(1, 0, amount)
    return (
        swap_amount
        if interface.ICurveV2Pool(CURVE_CVX_PCVX_POOL).price_oracle() > 1e18
        else amount
    )


def get_pcvx_to_cvx(amount):
    return (
        interface.ICurveV2Pool(CURVE_CVX_PCVX_POOL).get_dy(0, 1, amount)
        if amount > 0
        else 0
    )


def estimate_output_cvx_amount(tokens, union_contract, router_choices, gas_fee, lock):
    eth_amount = 0
    cvx_amount = 0
    for token in tokens:
        if token == CRV:
            eth_amount += get_crv_to_eth_amount(CLAIM_AMOUNT)
        if token == CVXCRV:
            eth_amount += get_crv_to_eth_amount(cvxcrv_to_crv(CLAIM_AMOUNT))
        if token == CVX:
            cvx_amount += CLAIM_AMOUNT
        elif token == WETH:
            eth_amount += CLAIM_AMOUNT - 1
        else:
            choice = router_choices & 7
            if choice >= 4:
                pool, index = CURVE_CONTRACT_REGISTRY[token.lower()]
                eth_amount += interface.ICurveV2Pool(pool).get_dy(
                    index ^ 1, index, CLAIM_AMOUNT - 1
                )
            elif choice == 2:
                eth_amount += interface.IQuoter(UNI_QUOTER).quoteExactInputSingle(
                    token, WETH, 3000, CLAIM_AMOUNT - 1, 0
                )
            elif choice == 3:
                eth_amount += interface.IQuoter(UNI_QUOTER).quoteExactInputSingle(
                    token, WETH, 10000, CLAIM_AMOUNT - 1, 0
                )
            else:
                router = UNI_ROUTER if (choice == 1) else SUSHI_ROUTER
                print(
                    f"Token: {token} swapped on {'Uni' if router == UNI_ROUTER else 'Sushi'}"
                )
                eth_amount += interface.IUniV2Router(router).getAmountsOut(
                    CLAIM_AMOUNT - 1, [token, WETH]
                )[-1]
        router_choices = router_choices // 8

    eth_amount -= gas_fee
    print("ETH Amount: ", eth_amount)

    swap_cvx_amount = interface.ICurveV2Pool(CURVE_CVX_ETH_POOL).get_dy(
        0, 1, eth_amount, {"from": union_contract}
    )
    cvx_amount += swap_cvx_amount
    print("CVX Amount: ", cvx_amount)

    if lock:
        cvx_amount = interface.ICurveV2Pool(CURVE_CVX_PCVX_POOL).get_dy(
            0, 1, cvx_amount
        )

    return cvx_amount
