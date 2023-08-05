from brownie import interface, chain
from eth_abi.packed import encode_single_packed

from .constants import (
    CVXFXS_STAKING_CONTRACT,
    CURVE_CVX_ETH_POOL,
    CURVE_CRV_ETH_POOL,
    CURVE_FXS_ETH_POOL,
    CURVE_CVXFXS_FXS_POOL,
    FXS,
    FXS_COMMUNITY,
    CURVE_CVXFXS_FXS_LP_TOKEN,
    UNI_QUOTER,
    WETH,
    FRAX,
    USDC,
    UNI_ROUTER,
    CVXFXS,
    CVXFXS_FXS_GAUGE_DEPOSIT,
    CVX_MINING_LIB,
    CURVE_FRAX_USDC_POOL,
    CRV_TOKEN,
    CVX, CURVE_TRICRV_POOL,
)

random_wallet = "0xBa90C1f2B5678A055467Ed2d29ab66ed407Ba8c6"


def estimate_underlying_received(amount, token_index):
    interface.IERC20(CURVE_CVXFXS_FXS_LP_TOKEN).approve(
        CURVE_CVXFXS_FXS_POOL, 2**256 - 1, {"from": CVXFXS_FXS_GAUGE_DEPOSIT}
    )
    tx = interface.ICurveV2Pool(CURVE_CVXFXS_FXS_POOL).remove_liquidity_one_coin(
        amount, token_index, 0, False, random_wallet, {"from": CVXFXS_FXS_GAUGE_DEPOSIT}
    )
    value = tx.return_value
    # older version of brownie bork the return value
    if value is None:
        value = tx.events[-1]["coin_amount"]
    chain.undo(2)
    return value


def estimate_lp_tokens_received(amount, amount_cvxfxs=0):
    lpt = interface.IERC20(CURVE_CVXFXS_FXS_LP_TOKEN)
    fxs = interface.IERC20(FXS)
    if amount == 0 and amount_cvxfxs == 0:
        return 0

    if amount > 0:
        fxs.approve(CURVE_CVXFXS_FXS_POOL, 2**256 - 1, {"from": random_wallet})
        fxs.transfer(random_wallet, amount, {"from": FXS_COMMUNITY})

    if amount_cvxfxs > 0:
        interface.IERC20(CVXFXS).transfer(
            random_wallet, amount_cvxfxs, {"from": CURVE_CVXFXS_FXS_POOL}
        )
        interface.IERC20(CVXFXS).approve(
            CURVE_CVXFXS_FXS_POOL, 2**256 - 1, {"from": random_wallet}
        )

    interface.ICurveV2Pool(CURVE_CVXFXS_FXS_POOL).add_liquidity(
        [amount, amount_cvxfxs], 0, {"from": random_wallet}
    )
    tokens_added = lpt.balanceOf(random_wallet)
    chain.undo(3)
    return tokens_added


def calc_rewards(strategy):
    staking = interface.IBasicRewards(CVXFXS_STAKING_CONTRACT)
    crv_rewards = staking.earned(strategy)
    cvx_rewards = interface.ICvxMining(CVX_MINING_LIB).ConvertCrvToCvx(crv_rewards)
    cvx_rewards += interface.IBasicRewards(staking.extraRewards(0)).earned(strategy)
    fxs_rewards = interface.IBasicRewards(staking.extraRewards(1)).earned(strategy)

    eth_balance = get_cvx_to_eth_amount(cvx_rewards)
    eth_balance += get_crv_to_eth_amount(crv_rewards)

    return fxs_rewards, eth_balance


def get_cvx_to_eth_amount(amount):
    cvx_eth_swap = interface.ICurveV2Pool(CURVE_CVX_ETH_POOL)
    return cvx_eth_swap.get_dy(1, 0, amount) if amount > 0 else 0


def get_crv_to_eth_amount(amount):
    crv_eth_swap = interface.ICurveTriCryptoFactoryNG(CURVE_TRICRV_POOL)
    return crv_eth_swap.get_dy(2, 1, amount) if amount > 0 else 0


def eth_fxs_uniswap(amount):
    return interface.IQuoter(UNI_QUOTER).quoteExactInputSingle(
        WETH, FXS, 10000, amount, 0
    )


def fxs_eth_uniswap(amount):
    return interface.IQuoter(UNI_QUOTER).quoteExactInputSingle(
        FXS, WETH, 10000, amount, 0
    )


def calc_harvest_amount_uniswap(strategy):
    fxs_balance, eth_balance = calc_rewards(strategy)
    if eth_balance > 0:
        fxs_balance += eth_fxs_uniswap(eth_balance)

    return fxs_balance


def fxs_eth_unicurve1(amount):
    frax_balance = interface.IUniV2Router(UNI_ROUTER).getAmountsOut(
        amount, [FXS, FRAX]
    )[-1]
    usdc_balance = interface.ICurvePool(CURVE_FRAX_USDC_POOL).get_dy(0, 1, frax_balance)
    path = encode_single_packed("(address,uint24,address)", [USDC, 500, WETH])
    return interface.IQuoter(UNI_QUOTER).quoteExactInput(path, usdc_balance)


def eth_fxs_unicurve1(amount):
    path = encode_single_packed("(address,uint24,address)", [WETH, 500, USDC])
    usdc_balance = interface.IQuoter(UNI_QUOTER).quoteExactInput(path, amount)
    frax_balance = interface.ICurvePool(CURVE_FRAX_USDC_POOL).get_dy(1, 0, usdc_balance)
    return interface.IUniV2Router(UNI_ROUTER).getAmountsOut(frax_balance, [FRAX, FXS])[
        -1
    ]


def eth_fxs_unistable(amount):
    path = encode_single_packed(
        "(address,uint24,address,uint24,address)", [WETH, 500, USDC, 500, FRAX]
    )
    stable_balance = interface.IQuoter(UNI_QUOTER).quoteExactInput(path, amount)
    return interface.IUniV2Router(UNI_ROUTER).getAmountsOut(
        stable_balance, [FRAX, FXS]
    )[-1]


def fxs_eth_unistable(amount):
    stable_balance = interface.IUniV2Router(UNI_ROUTER).getAmountsOut(
        amount, [FXS, FRAX]
    )[-1]
    path = encode_single_packed(
        "(address,uint24,address,uint24,address)", [FRAX, 500, USDC, 500, WETH]
    )
    return interface.IQuoter(UNI_QUOTER).quoteExactInput(path, stable_balance)


def calc_harvest_amount_unistable(strategy):
    fxs_balance, eth_balance = calc_rewards(strategy)
    if eth_balance > 0:
        fxs_balance += eth_fxs_unistable(eth_balance)

    return fxs_balance


def eth_fxs_curve(amount):
    return (
        interface.ICurveV2Pool(CURVE_FXS_ETH_POOL).get_dy(0, 1, amount)
        if amount > 0
        else 0
    )


def fxs_eth_curve(amount):
    return (
        interface.ICurveV2Pool(CURVE_FXS_ETH_POOL).get_dy(1, 0, amount)
        if amount > 0
        else 0
    )


def calc_harvest_amount_curve(strategy):

    fxs_balance, eth_balance = calc_rewards(strategy)
    if eth_balance > 0:
        fxs_balance += eth_fxs_curve(eth_balance)

    return fxs_balance


def fxs_to_cvxfxs(amount):
    return interface.ICurveV2Pool(CURVE_CVXFXS_FXS_POOL).get_dy(0, 1, amount)


def cvxfxs_to_fxs(amount):
    return interface.ICurveV2Pool(CURVE_CVXFXS_FXS_POOL).get_dy(1, 0, amount)


def calc_staking_harvest_amount(strategy, staking, option, lock=False):

    fxs_balance, eth_balance = calc_staking_rewards(strategy, staking)
    if eth_balance > 0:
        fxs_balance += eth_to_fxs(eth_balance, option)
    return fxs_balance if lock else fxs_to_cvxfxs(fxs_balance)


def calc_staking_rewards(strategy, staking):
    staking_rewards = staking.claimableRewards(strategy)
    eth_balance = 0
    fxs_rewards = 0
    for rewards in staking_rewards:
        token, amount = rewards
        if token == CRV_TOKEN:
            eth_balance += get_crv_to_eth_amount(amount)
        elif token == CVX:
            eth_balance += get_cvx_to_eth_amount(amount)
        elif token == FXS:
            fxs_rewards += amount

    return fxs_rewards, eth_balance


def eth_to_fxs(amount, option):
    if option == 0:
        return eth_fxs_curve(amount)
    elif option == 1:
        return eth_fxs_uniswap(amount)
    elif option == 3:
        return eth_fxs_unicurve1(amount)
    else:
        return eth_fxs_unistable(amount)


def fxs_to_eth(amount, option):
    if option == 0:
        return fxs_eth_curve(amount)
    elif option == 1:
        return fxs_eth_uniswap(amount)
    elif option == 3:
        return fxs_eth_unicurve1(amount)
    else:
        return fxs_eth_unistable(amount)
