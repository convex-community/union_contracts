from brownie import chain, interface, convert
import eth_abi
from tests.utils.constants import (
    AURA_BAL_STAKING,
    AURA_MINING_LIB,
    BAL_VAULT,
    AURA_ETH_POOL_ID,
    AURA_TOKEN,
    WETH,
    WSTETH_BBUSD_POOL_ID,
    WSTETH_WETH_POOL_ID,
    BBUSD_TOKEN,
    WSTETH_TOKEN,
    BAL_ETH_POOL_ID,
    BAL_TOKEN,
    BAL_ETH_POOL_TOKEN,
)


# currently not needed but might change
def get_minter_minted():
    return 0


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
    query = vault.queryBatchSwap(0, [swap_step], assets, funds)
    return query[-1] * -1


def get_bbusd_to_eth_amount(amount):
    vault = interface.IBalancerVault(BAL_VAULT)
    swap_steps = [
        (
            WSTETH_BBUSD_POOL_ID,
            2,  # BBUSD Index
            1,  # WSTETH Index
            amount,
            eth_abi.encode_abi(["uint256"], [0]),
        ),
        (
            WSTETH_WETH_POOL_ID,
            0,  # WSTETH Index
            1,  # WETH Index
            amount,
            eth_abi.encode_abi(["uint256"], [0]),
        ),
    ]
    assets = [BBUSD_TOKEN, WSTETH_TOKEN, WETH]
    funds = (WETH, False, WETH, False)
    query = vault.queryBatchSwap(0, swap_steps, assets, funds)
    return query[-1] * -1


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


def calc_harvest_amount_aura(strategy):
    bal_balance, eth_balance = calc_rewards(strategy)
    blp = interface.IBalancerPool(BAL_ETH_POOL_TOKEN)
    bp_out, _ = blp.queryJoin(
        BAL_ETH_POOL_ID,
        strategy.address,
        strategy.address,
        [bal_balance, eth_balance],
        (
            [BAL_TOKEN, WETH],
            [bal_balance, eth_balance],
            convert(1, [bal_balance, eth_balance]),
            False,
        ),
    )
    return bp_out
