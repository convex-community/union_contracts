import brownie
from brownie import network, chain, interface
from decimal import Decimal
import time
from ..utils import estimate_output_amount, approx
from ..utils.constants import (
    CLAIM_AMOUNT,
    SUSHI_ROUTER,
    TOKENS,
    ALCX,
    WETH,
    CVXCRV,
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
    network.gas_price("0 gwei")
    original_union_balance = interface.IERC20(CVXCRV).balanceOf(union_contract)
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

    expected_output_amount, eth_crv_ratio = estimate_output_amount(
        TOKENS, union_contract, 0
    )
    union_contract.setApprovals({"from": owner})

    # Manually handle ALCX swapping
    union_contract.claim(single_claim_param, {"from": owner})
    union_contract.retrieveTokens([ALCX], owner, {"from": owner})
    assert interface.IERC20(ALCX).balanceOf(owner) == CLAIM_AMOUNT
    interface.IERC20(ALCX).approve(SUSHI_ROUTER, 2 ** 256 - 1, {"from": owner})
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
    tx = union_contract.distribute(params, 0, True, False, True, 0, {"from": owner})
    distributor_balance = vault.balanceOfUnderlying(merkle_distributor_v2)
    union_balance = interface.IERC20(CVXCRV).balanceOf(union_contract)

    gas_used = tx.gas_price * tx.gas_used
    gas_fees = original_caller_balance - owner.balance() + gas_used
    gas_fees_in_crv = tx.events["Distributed"]["fees"]
    assert distributor_balance > 0
    assert union_balance == original_union_balance
    assert merkle_distributor_v2.frozen() == True
    assert gas_fees >= tx.gas_price
    assert merkle_distributor_v2.frozen() == True
    assert distributor_balance == expected_output_amount - gas_fees_in_crv
