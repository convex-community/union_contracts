import brownie
from brownie import interface, chain
from .constants import (
    CLAIM_AMOUNT,
    TOKENS,
    CVXCRV,
    SUSHI_ROUTER,
    UNI_ROUTER,
    WETH,
    CRV,
    CURVE_CVXCRV_CRV_POOL,
    ADDRESS_ZERO,
    CURVE_VOTING_ESCROW,
    CURVE_CVX_ETH_POOL,
    TRICRYPTO,
    TRIPOOL,
    UNI_QUOTER,
    CURVE_CVXFXS_FXS_LP_TOKEN,
    FXS,
    CURVE_CONTRACT_REGISTRY,
    CVX,
    CURVE_CVX_PCVX_POOL,
    AURA_BAL_TOKEN,
    BAL_ETH_POOL_TOKEN,
    CVXFXS,
    CURVE_CVXCRV_CRV_POOL_V2,
    CURVE_TRICRV_POOL,
    PRISMA,
    CVXPRISMA,
)
from .cvxfxs import get_crv_to_eth_amount


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
        interface.ICurveTriCryptoFactoryNG(CURVE_TRICRV_POOL).get_dy(1, 2, eth_balance)
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


def calc_staked_cvxcrv_harvest(strategy, wrapper, force_lock=False):
    earned = wrapper.earned(strategy, {"from": strategy}).return_value
    reward_amounts = [r[1] for r in earned]
    print("Rewards: ", earned)
    crv_balance, cvx_balance, three_crv_balance = reward_amounts

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
        interface.ICurveTriCryptoFactoryNG(CURVE_TRICRV_POOL).get_dy(1, 2, eth_balance)
        if eth_balance > 0
        else 0
    )

    cvxcrv_amount = crv_balance
    if crv_balance > 0:
        oracle = interface.ICurveNewFactoryPool(CURVE_CVXCRV_CRV_POOL_V2).price_oracle()
        if oracle < 1e18 and not force_lock:
            cvxcrv_amount = interface.ICurveNewFactoryPool(
                CURVE_CVXCRV_CRV_POOL_V2
            ).get_dy(0, 1, crv_balance)
            assert cvxcrv_amount > crv_balance

    return cvxcrv_amount


def aurabal_balance(address):
    return interface.IERC20(AURA_BAL_TOKEN).balanceOf(address)


def cvxcrv_balance(address):
    return interface.IERC20(CVXCRV).balanceOf(address)


def cvxfxs_lp_balance(address):
    return interface.IERC20(CURVE_CVXFXS_FXS_LP_TOKEN).balanceOf(address)


def baleth_lp_balance(address):
    return interface.IERC20(BAL_ETH_POOL_TOKEN).balanceOf(address)


def fxs_balance(address):
    return interface.IERC20(FXS).balanceOf(address)


def cvxfxs_balance(address):
    return interface.IERC20(CVXFXS).balanceOf(address)


def prisma_balance(address):
    return interface.IERC20(PRISMA).balanceOf(address)


def cvxprisma_balance(address):
    return interface.IERC20(CVXPRISMA).balanceOf(address)


def approx(a, b, precision=1e-10):
    if a == b == 0:
        return True
    return 2 * abs(a - b) / (a + b) <= precision


def estimate_amounts_after_swap(tokens, union_contract, router_choices, weights):
    def is_effective_output_token(token, weights):
        for i in range(len(weights)):
            if union_contract.outputTokens(i) == token and weights[i] > 0:
                return True
        return False

    eth_amount = 0
    for i, token in enumerate(tokens):
        if token == WETH:
            eth_amount += CLAIM_AMOUNT - 1
        else:
            if is_effective_output_token(token, weights):
                continue

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

    print("ETH Amount: ", eth_amount)
    return eth_amount


def crv_to_cvxcrv(amount):
    return interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(0, 1, amount)


def crv_to_cvxcrv_v2(amount):
    return interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL_V2).get_dy(0, 1, amount)


def cvxcrv_to_crv(amount):
    return interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL).get_dy(1, 0, amount)


def cvxcrv_to_crv_v2(amount):
    return interface.ICurveFactoryPool(CURVE_CVXCRV_CRV_POOL_V2).get_dy(1, 0, amount)


def eth_to_cvxcrv(amount):
    return crv_to_cvxcrv(eth_to_crv(amount))


def eth_to_cvxcrv_v2(amount):
    return crv_to_cvxcrv_v2(eth_to_crv(amount))


def eth_to_crv(amount):
    if amount <= 0:
        return 0
    return interface.ICurveTriCryptoFactoryNG(CURVE_TRICRV_POOL).get_dy(1, 2, amount)


def eth_to_cvx(amount):
    if amount <= 0:
        return 0
    return interface.ICurveV2Pool(CURVE_CVX_ETH_POOL).get_dy(0, 1, amount)
