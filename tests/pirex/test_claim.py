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
)
from ..utils.pirex import estimate_output_cvx_amount


@pytest.mark.parametrize("lock", [True, False])
def test_claim_sushi(
    fn_isolation,
    owner,
    union_contract,
    set_mock_claims,
    claim_tree,
    pirex_strategy,
    lock,
):
    initial_reward_rate = pirex_strategy.rewardRate()
    initial_last_updated = pirex_strategy.lastUpdateTime()
    initial_strat_balance = interface.IERC20(PXCVX_TOKEN).balanceOf(pirex_strategy)
    owner_original_balance = owner.balance()
    gas_refund = 1e10
    proofs = claim_tree.get_proof(union_contract.address)
    params = [
        [token, proofs["claim"]["index"], CLAIM_AMOUNT, proofs["proofs"]]
        for token in TOKENS
    ]

    expected_output_amount = estimate_output_cvx_amount(
        TOKENS, union_contract, 0, gas_refund, lock
    )

    tx = union_contract.distribute(
        params, 0, True, lock, True, 0, gas_refund, {"from": owner}
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
