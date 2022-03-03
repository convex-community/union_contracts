import brownie
from brownie import interface
from .constants import (
    CLAIM_AMOUNT,
    TOKENS,
    CVXCRV,
    SUSHI_ROUTER,
    UNI_ROUTER,
    WETH,
    CRV,
    CURVE_CRV_ETH_POOL,
    CURVE_CVXCRV_CRV_POOL,
    ADDRESS_ZERO,
    CURVE_VOTING_ESCROW,
    CURVE_CVX_ETH_POOL,
    TRICRYPTO,
    TRIPOOL,
    UNI_QUOTER,
    CURVE_CVXFXS_FXS_LP_TOKEN,
    FXS,
)


def calc_harvest_amount_in_cvxcrv(vault):
    three_crv_balance = vault.outstanding3CrvRewards()
    cvx_balance = vault.outstandingCvxRewards()
    crv_balance = vault.outstandingCrvRewards()

    cvxEthSwap = interface.ICurveV2Pool(CURVE_CVX_ETH_POOL)
    tripool = interface.ICurvePool(TRIPOOL)
    tricrypto = interface.ICurveTriCrypto(TRICRYPTO)

    eth_balance = cvxEthSwap.get_dy(1, 0, cvx_balance) if cvx_balance > 0 else 0
    usdt_balance = (
        tripool.calc_withdraw_one_coin(three_crv_balance, 2)
        if three_crv_balance > 0
        else 0
    )
    eth_balance += tricrypto.get_dy(0, 2, usdt_balance) if usdt_balance > 0 else 0
    crv_balance += (
        interface.ICurveV2Pool(CURVE_CRV_ETH_POOL).get_dy(0, 1, eth_balance)
        if eth_balance > 0
        else 0
    )

    cvxcrv_amount = crv_balance
    if crv_balance > 0:
        quote = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(
            0, 1, crv_balance
        )
        if quote > crv_balance:
            cvxcrv_amount = quote
    return cvxcrv_amount


def cvxcrv_balance(address):
    return interface.IERC20(CVXCRV).balanceOf(address)


def cvxfxs_lp_balance(address):
    return interface.IERC20(CURVE_CVXFXS_FXS_LP_TOKEN).balanceOf(address)


def fxs_balance(address):
    return interface.IERC20(FXS).balanceOf(address)


def approx(a, b, precision=1e-10):
    if a == b == 0:
        return True
    return 2 * abs(a - b) / (a + b) <= precision


def estimate_output_amount(tokens, union_contract, router_choices):
    eth_amount = 0
    crv_amount = 0
    for token in tokens:
        if token == CRV:
            crv_amount += CLAIM_AMOUNT
        elif token == WETH:
            eth_amount += CLAIM_AMOUNT - 1
        else:
            if router_choices & 3 == 2:
                eth_amount += interface.IQuoter(UNI_QUOTER).quoteExactInputSingle(
                    token, WETH, 3000, CLAIM_AMOUNT - 1, 0
                )
            elif router_choices & 3 == 3:
                eth_amount += interface.IQuoter(UNI_QUOTER).quoteExactInputSingle(
                    token, WETH, 10000, CLAIM_AMOUNT - 1, 0
                )
            else:
                router = UNI_ROUTER if (router_choices & 3 == 1) else SUSHI_ROUTER
                print(
                    f"Token: {token} swapped on {'Uni' if router == UNI_ROUTER else 'Sushi'}"
                )
                eth_amount += interface.IUniV2Router(router).getAmountsOut(
                    CLAIM_AMOUNT - 1, [token, WETH]
                )[-1]
        router_choices = router_choices // 4

    print("ETH Amount: ", eth_amount)

    swap_crv_amount = interface.ICurveV2Pool(CURVE_CRV_ETH_POOL).get_dy(
        0, 1, eth_amount, {"from": union_contract}
    )
    crv_amount += swap_crv_amount
    eth_crv_ratio = swap_crv_amount / eth_amount
    print("CRV Amount: ", crv_amount)

    quote = interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(0, 1, crv_amount)
    cvxcrv_amount = crv_amount
    if quote > crv_amount:
        cvxcrv_amount = quote
    if CVXCRV in tokens:
        cvxcrv_amount += CLAIM_AMOUNT
    return cvxcrv_amount, eth_crv_ratio
