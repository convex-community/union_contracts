from brownie import chain, interface, convert, accounts
import eth_abi
from tests.utils.constants import (
    AURA_BAL_STAKING,
    AURA_MINING_LIB,
    BAL_VAULT,
    AURA_ETH_POOL_ID,
    AURA_TOKEN,
    WETH,
    BBUSD_TOKEN,
    BAL_ETH_POOL_ID,
    BAL_TOKEN,
    ETH_USDC_POOL_ID,
    BBUSDC_USDC_POOL_ID,
    BBUSD_AAVE_POOL_ID,
    BBUSDC_TOKEN,
    USDC_TOKEN,
    BALANCER_HELPER,
    BAL_ETH_POOL_TOKEN,
    AURA_BAL_TOKEN,
    AURABAL_BAL_ETH_BPT_POOL_ID,
    AURABAL_TOKEN,
)


# currently not needed but might change
def get_minter_minted():
    return 0


def get_aurabal_to_lptoken_amount(amount):
    vault = interface.IBalancerVault(BAL_VAULT)
    swap_step = (
        AURABAL_BAL_ETH_BPT_POOL_ID,
        0,
        1,
        amount,
        eth_abi.encode_abi(["uint256"], [0]),
    )
    assets = [AURA_BAL_TOKEN, BAL_ETH_POOL_TOKEN]
    funds = (WETH, False, WETH, False)
    query = vault.queryBatchSwap(0, [swap_step], assets, funds, {"from": accounts[0]})
    # assert False == True
    return query.return_value[-1] * -1


def get_aura_to_eth_amount(amount):
    vault = interface.IBalancerVault(BAL_VAULT)
    swap_step = (
        AURA_ETH_POOL_ID,
        0,  # AURA Index
        1,  # WETH Index
        amount,
        eth_abi.encode_abi(["uint256"], [0]),
    )
    assets = [AURA_TOKEN, WETH]
    funds = (WETH, False, WETH, False)
    query = vault.queryBatchSwap(0, [swap_step], assets, funds, {"from": accounts[0]})
    return query.return_value[-1] * -1


def get_bbusd_to_eth_amount(amount):
    vault = interface.IBalancerVault(BAL_VAULT)
    assets = [BBUSD_TOKEN, BBUSDC_TOKEN, USDC_TOKEN, WETH]
    indices = {assets[idx]: idx for idx in range(len(assets))}

    swap_steps = [
        (
            BBUSD_AAVE_POOL_ID,
            indices[BBUSD_TOKEN],
            indices[BBUSDC_TOKEN],
            amount,
            eth_abi.encode_abi(["uint256"], [0]),
        ),
        (
            BBUSDC_USDC_POOL_ID,
            indices[BBUSDC_TOKEN],
            indices[USDC_TOKEN],
            0,
            eth_abi.encode_abi(["uint256"], [0]),
        ),
        (
            ETH_USDC_POOL_ID,
            indices[USDC_TOKEN],
            indices[WETH],
            0,
            eth_abi.encode_abi(["uint256"], [0]),
        ),
    ]

    funds = (WETH, False, WETH, False)
    query = vault.queryBatchSwap(0, swap_steps, assets, funds, {"from": accounts[0]})
    return query.return_value[-1] * -1


def calc_rewards(strategy):
    staking = interface.IBasicRewards(AURA_BAL_STAKING)
    bal_rewards = staking.earned(strategy)
    aura_rewards = interface.IAuraMining(AURA_MINING_LIB).ConvertBalToAura(
        bal_rewards, get_minter_minted()
    )
    bbusd_rewards = interface.IBasicRewards(staking.extraRewards(0)).earned(strategy)

    eth_balance = get_aura_to_eth_amount(aura_rewards)
    eth_balance += get_bbusd_to_eth_amount(bbusd_rewards)

    return bal_rewards, eth_balance


def estimate_wethbal_lp_tokens_received(strategy, bal_balance, eth_balance):
    blp = interface.IBalancerHelper(BALANCER_HELPER)
    tokens = [BAL_TOKEN, WETH]
    amounts = [bal_balance, eth_balance]

    join_request = (
        tokens,
        amounts,
        eth_abi.encode_abi(
            ["uint256", "uint256[]"], [1, [bal_balance, eth_balance]]
        ).hex(),
        False,
    )

    bp_out, _ = blp.queryJoin(
        BAL_ETH_POOL_ID,
        strategy.address,
        strategy.address,
        join_request,
    )
    return bp_out


def estimate_underlying_received_baleth(strategy, lp_amount, asset_index):
    blp = interface.IBalancerHelper(BALANCER_HELPER)
    tokens = [BAL_TOKEN, WETH]
    amounts = [0, 0]

    exit_request = (
        tokens,
        amounts,
        eth_abi.encode_abi(
            ["uint256", "uint256", "uint256"], [0, lp_amount, asset_index]
        ).hex(),
        False,
    )

    _, query = blp.queryExit(
        BAL_ETH_POOL_ID,
        strategy.address,
        strategy.address,
        exit_request,
    )
    token_out = query[asset_index]
    return token_out


def get_blp_to_aurabal(amount):
    vault = interface.IBalancerVault(BAL_VAULT)
    swap_step = (
        AURABAL_BAL_ETH_BPT_POOL_ID,
        0,
        1,
        amount,
        eth_abi.encode_abi(["uint256"], [0]),
    )
    assets = [BAL_ETH_POOL_TOKEN, AURABAL_TOKEN]
    funds = (WETH, False, WETH, False)
    query = vault.queryBatchSwap(0, [swap_step], assets, funds, {"from": accounts[0]})
    return query.return_value[-1] * -1


def calc_harvest_amount_aura(strategy, lock=True):
    bal_balance, eth_balance = calc_rewards(strategy)
    blp_tokens = estimate_wethbal_lp_tokens_received(strategy, bal_balance, eth_balance)
    if lock:
        return blp_tokens
    else:
        return get_blp_to_aurabal(blp_tokens)
