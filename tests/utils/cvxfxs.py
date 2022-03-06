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
    USDT,
    UNI_ROUTER,
    CVXFXS,
)


def estimate_lp_tokens_received(amount, amount_cvxfxs=0):
    lpt = interface.IERC20(CURVE_CVXFXS_FXS_LP_TOKEN)
    random_wallet = "0xBa90C1f2B5678A055467Ed2d29ab66ed407Ba8c6"
    fxs = interface.IERC20(FXS)
    if amount == 0 and amount_cvxfxs == 0:
        return 0

    if amount > 0:
        fxs.approve(CURVE_CVXFXS_FXS_POOL, 2 ** 256 - 1, {"from": random_wallet})
        fxs.transfer(random_wallet, amount, {"from": FXS_COMMUNITY})

    if amount_cvxfxs > 0:
        interface.IERC20(CVXFXS).transfer(
            random_wallet, amount_cvxfxs, {"from": CURVE_CVXFXS_FXS_POOL}
        )
        interface.IERC20(CVXFXS).approve(
            CURVE_CVXFXS_FXS_POOL, 2 ** 256 - 1, {"from": random_wallet}
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
    cvx_rewards = interface.IBasicRewards(staking.extraRewards(0)).earned(strategy)
    fxs_rewards = interface.IBasicRewards(staking.extraRewards(1)).earned(strategy)

    eth_balance = get_cvx_to_eth_amount(cvx_rewards)
    eth_balance += get_crv_to_eth_amount(crv_rewards)

    return fxs_rewards, eth_balance


def get_cvx_to_eth_amount(amount):
    cvx_eth_swap = interface.ICurveV2Pool(CURVE_CVX_ETH_POOL)
    return cvx_eth_swap.get_dy(1, 0, amount) if amount > 0 else 0


def get_crv_to_eth_amount(amount):
    crv_eth_swap = interface.ICurveV2Pool(CURVE_CRV_ETH_POOL)
    return crv_eth_swap.get_dy(1, 0, amount) if amount > 0 else 0


def eth_fxs_uniswap(amount):
    return interface.IQuoter(UNI_QUOTER).quoteExactInputSingle(
        WETH, FXS, 10000, amount, 0
    )


def calc_harvest_amount_uniswap(strategy):
    fxs_balance, eth_balance = calc_rewards(strategy)
    if eth_balance > 0:
        fxs_balance += eth_fxs_uniswap(eth_balance)

    return fxs_balance


def eth_fxs_unistable(amount):
    path = encode_single_packed(
        "(address,uint24,address,uint24,address)", [WETH, 500, USDT, 500, FRAX]
    )
    stable_balance = interface.IQuoter(UNI_QUOTER).quoteExactInput(path, amount)
    return interface.IUniV2Router(UNI_ROUTER).getAmountsOut(
        stable_balance, [FRAX, FXS]
    )[-1]


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


def calc_harvest_amount_curve(strategy):

    fxs_balance, eth_balance = calc_rewards(strategy)
    if eth_balance > 0:
        fxs_balance += eth_fxs_curve(eth_balance)

    return fxs_balance
