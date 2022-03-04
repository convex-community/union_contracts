from brownie import interface, chain

from .constants import (
    CVXFXS_STAKING_CONTRACT,
    CURVE_CVX_ETH_POOL,
    CURVE_CRV_ETH_POOL,
    CURVE_FXS_ETH_POOL,
    CURVE_CVXFXS_FXS_POOL,
    FXS,
    FXS_COMMUNITY,
    CURVE_CVXFXS_FXS_LP_TOKEN,
)


def estimate_lp_tokens_received(amount):
    random_wallet = "0xBa90C1f2B5678A055467Ed2d29ab66ed407Ba8c6"
    fxs = interface.IERC20(FXS)
    lpt = interface.IERC20(CURVE_CVXFXS_FXS_LP_TOKEN)
    fxs.approve(CURVE_CVXFXS_FXS_POOL, 2 ** 256 - 1, {"from": random_wallet})
    fxs.transfer(random_wallet, amount, {"from": FXS_COMMUNITY})
    interface.ICurveV2Pool(CURVE_CVXFXS_FXS_POOL).add_liquidity(
        [amount, 0], 0, {"from": random_wallet}
    )
    tokens_added = lpt.balanceOf(random_wallet)
    chain.undo(3)
    return tokens_added


def calc_harvest_amount_curve(strategy, fxs=False):

    staking = interface.IBasicRewards(CVXFXS_STAKING_CONTRACT)
    crv_rewards = staking.earned(strategy)
    cvx_rewards = interface.IBasicRewards(staking.extraRewards(0)).earned(strategy)
    fxs_rewards = interface.IBasicRewards(staking.extraRewards(1)).earned(strategy)

    cvx_eth_swap = interface.ICurveV2Pool(CURVE_CVX_ETH_POOL)
    crv_eth_swap = interface.ICurveV2Pool(CURVE_CRV_ETH_POOL)

    eth_balance = cvx_eth_swap.get_dy(1, 0, cvx_rewards) if cvx_rewards > 0 else 0
    if crv_rewards > 0:
        eth_balance += crv_eth_swap.get_dy(1, 0, crv_rewards)

    fxs_balance = fxs_rewards
    if eth_balance > 0:
        fxs_balance += interface.ICurveV2Pool(CURVE_FXS_ETH_POOL).get_dy(
            0, 1, eth_balance
        )
    if fxs:
        return fxs_balance

    return estimate_lp_tokens_received(fxs_balance)
