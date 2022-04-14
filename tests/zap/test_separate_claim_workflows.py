import brownie
from brownie import network, chain, interface
from decimal import Decimal
import time
from ..utils import estimate_output_amount, approx, estimate_amounts_after_swap
from ..utils.constants import (
    CLAIM_AMOUNT,
    SUSHI_ROUTER,
    TOKENS,
    ALCX,
    WETH,
    CVXCRV,
    MAX_UINT256,
)


def test_manual_claim_workflow(
    fn_isolation,
    owner,
    union_contract,
    set_mock_claims,
    claim_tree,
    merkle_distributor_v2,
    vault,
):
    weights = [10000, 0, 0]
    network.gas_price("0 gwei")
    proofs = claim_tree.get_proof(union_contract.address)
    params = [
        [token, proofs["claim"]["index"], CLAIM_AMOUNT, proofs["proofs"]]
        for token in TOKENS
        if token != ALCX
    ]
    single_claim_param = [
        [token, proofs["claim"]["index"], CLAIM_AMOUNT, proofs["proofs"]]
        for token in TOKENS
        if token == ALCX
    ]

    expected_eth_amount = estimate_amounts_after_swap(
        TOKENS, union_contract, 0, weights
    )

    # Manually handle ALCX swapping
    union_contract.claim(single_claim_param, {"from": owner})
    union_contract.retrieveTokens([ALCX], owner, {"from": owner})
    assert interface.IERC20(ALCX).balanceOf(owner) == CLAIM_AMOUNT
    interface.IERC20(ALCX).approve(SUSHI_ROUTER, MAX_UINT256, {"from": owner})
    single_swap_tx = interface.IUniV2Router(SUSHI_ROUTER).swapExactTokensForETH(
        CLAIM_AMOUNT,
        0,
        [ALCX, WETH],
        owner.address,
        int(time.time() + 120),
        {"from": owner},
    )
    eth_amount = single_swap_tx.return_value[-1]
    owner.transfer(union_contract, eth_amount)
    original_caller_balance = owner.balance()

    tx_swap = union_contract.swap(params, 0, False, 0, weights, {"from": owner})
    gas_fees = owner.balance() - original_caller_balance

    assert union_contract.balance() == expected_eth_amount + eth_amount - gas_fees
