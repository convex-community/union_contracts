import brownie
from brownie import interface, chain, network
import pytest
from ..utils import approx, eth_to_cvxcrv
from ..utils.constants import (
    CLAIM_AMOUNT,
    TOKENS,
    CVXCRV_REWARDS,
    CVXCRV,
    PIREX_CVX_STRATEGY,
    PXCVX_TOKEN,
    WETH,
    VOTIUM_DISTRIBUTOR,
    BAL_VAULT,
)
from ..utils.pirex import estimate_output_cvx_amount


def mock_distribute(union_contract, token_list):
    interface.IERC20(WETH).transfer(VOTIUM_DISTRIBUTOR, 1e20, {"from": BAL_VAULT})
    for token in token_list:
        interface.IERC20(token).transfer(
            union_contract, CLAIM_AMOUNT, {"from": VOTIUM_DISTRIBUTOR}
        )


@pytest.mark.parametrize("lock", [True, False])
def test_claim_sushi(
    fn_isolation,
    owner,
    union_contract,
    pirex_strategy,
    lock,
):
    initial_reward_rate = pirex_strategy.rewardRate()
    initial_last_updated = pirex_strategy.lastUpdateTime()
    initial_strat_balance = interface.IERC20(PXCVX_TOKEN).balanceOf(pirex_strategy)
    owner_original_balance = owner.balance()
    gas_refund = 1e10

    mock_distribute(union_contract, TOKENS)

    expected_output_amount = estimate_output_cvx_amount(
        TOKENS, union_contract, 0, gas_refund, lock
    )

    tx = union_contract.distribute(
        1,
        [0] * len(TOKENS),
        TOKENS,
        0,
        False,
        lock,
        True,
        0,
        gas_refund,
        {"from": owner},
    )
    strat_balance_after_deposit = interface.IERC20(PXCVX_TOKEN).balanceOf(
        pirex_strategy
    )

    new_reward_rate = pirex_strategy.rewardRate()
    new_last_updated = pirex_strategy.lastUpdateTime()

    assert owner_original_balance + gas_refund == owner.balance()
    assert approx(
        strat_balance_after_deposit - initial_strat_balance,
        expected_output_amount,
        1e-2,
    )
    assert new_reward_rate > initial_reward_rate
    assert new_last_updated > initial_last_updated
