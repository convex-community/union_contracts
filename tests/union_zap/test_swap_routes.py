import brownie
import pytest
import random
from pytest_lazyfixture import lazy_fixture
from brownie import interface, network
import pytest

from ..utils import (
    estimate_amounts_after_swap,
)
from ..utils.constants import (
    CLAIM_AMOUNT,
    V3_TOKENS,
    V3_1_TOKENS,
    CURVE_TOKENS,
    CURVE_CONTRACT_REGISTRY,
    UNIV3_ROUTER,
    REGULAR_TOKENS,
    UNI_ROUTER,
    FXS,
    ALCX,
    SUSHI_ROUTER,
    MAX_WEIGHT_1E9,
)

data = [
    [MAX_WEIGHT_1E9, 0, 0, 0],
    [0, MAX_WEIGHT_1E9, 0, 0],
    [0, 0, MAX_WEIGHT_1E9, 0],
    [300000000, 500000000, 100000000, 100000000],
]
curve_routers = [value[0] for value in CURVE_CONTRACT_REGISTRY.values()]
claimable_tokens_params = [
    (REGULAR_TOKENS, 1, [UNI_ROUTER], lazy_fixture("set_mock_claims_regular")),
    (V3_TOKENS, 2, [UNIV3_ROUTER], lazy_fixture("set_mock_claims_v3")),
    (V3_1_TOKENS, 3, [UNIV3_ROUTER], lazy_fixture("set_mock_claims_v3_1")),
    (CURVE_TOKENS, 4, curve_routers, lazy_fixture("set_mock_claims_curve")),
]


@pytest.mark.parametrize("weights", data)
@pytest.mark.parametrize(
    "votium_tokens,bitmap_index,routers,mock_claims", claimable_tokens_params
)
def test_swap_routes(
    fn_isolation,
    owner,
    union_contract,
    set_mock_claims,
    claim_tree,
    weights,
    votium_tokens,
    bitmap_index,
    routers,
    mock_claims,
):
    output_tokens = [union_contract.outputTokens(i) for i in range(len(weights))]
    gas_refund = 3e16
    proofs = claim_tree.get_proof(union_contract.address)
    params = [
        [token, proofs["claim"]["index"], CLAIM_AMOUNT, proofs["proofs"]]
        for token in votium_tokens
    ]
    # using the summation sum{0,n}(k*8**i)
    router_choices = ((8 ** len(params) - 1) * bitmap_index) // 7

    expected_eth_amount = estimate_amounts_after_swap(
        votium_tokens, union_contract, router_choices, weights
    )
    original_caller_balance = owner.balance()
    expected_output_token_balances = []
    for i, weight in enumerate(weights):
        expected_balance = (
            0
            if weight == 0
            else CLAIM_AMOUNT
            if output_tokens[i] in votium_tokens
            else 0
        )
        expected_output_token_balances.append(expected_balance)

    tx_swap = union_contract.swap(
        params, router_choices, True, 0, gas_refund, weights, {"from": owner}
    )
    gas_fees = owner.balance() - original_caller_balance
    assert gas_fees == gas_refund
    assert union_contract.balance() == expected_eth_amount - gas_fees

    for i, expected_balance in enumerate(expected_output_token_balances):
        assert expected_balance == interface.IERC20(output_tokens[i]).balanceOf(
            union_contract
        ) or expected_balance + 1 == interface.IERC20(output_tokens[i]).balanceOf(
            union_contract
        )

    for approval in tx_swap.events["Approval"]:
        guy = "guy" if "guy" in approval else "spender"
        assert approval[guy] in routers


def test_swap_mixed_routes(
    fn_isolation, owner, union_contract, set_mock_claims_curve, claim_tree
):

    OTHER_TOKENS = [ALCX, FXS]
    weights = [MAX_WEIGHT_1E9, 0, 0, 0]
    gas_refund = 3e16

    proofs = claim_tree.get_proof(union_contract.address)
    params = [
        [token, proofs["claim"]["index"], CLAIM_AMOUNT, proofs["proofs"]]
        for token in CURVE_TOKENS + OTHER_TOKENS
    ]

    routers = [4 for _ in CURVE_TOKENS] + [random.randint(0, 2) for _ in OTHER_TOKENS]
    router_choices = sum([8**i * router for i, router in enumerate(routers)])
    print(f"ROUTER CHOICES: {router_choices} ({routers})")

    expected_eth_amount = estimate_amounts_after_swap(
        CURVE_TOKENS + OTHER_TOKENS, union_contract, router_choices, weights
    )

    original_caller_balance = owner.balance()

    tx_swap = union_contract.swap(
        params, router_choices, True, 0, gas_refund, weights, {"from": owner}
    )
    gas_fees = owner.balance() - original_caller_balance
    assert gas_fees == gas_refund
    assert union_contract.balance() == expected_eth_amount - gas_fees

    index = 0
    for approval in tx_swap.events["Approval"]:
        wad = "wad" if "wad" in approval else "value"
        guy = "guy" if "guy" in approval else "spender"
        if approval[wad] != CLAIM_AMOUNT - 1:
            continue
        elif routers[index] == 1:
            assert approval[guy] == UNI_ROUTER
        elif routers[index] == 2:
            assert approval[guy] == UNIV3_ROUTER
        elif routers[index] == 3:
            assert approval[guy] == UNIV3_ROUTER
        elif routers[index] == 4:
            assert approval[guy] in curve_routers
        else:
            assert approval[guy] == SUSHI_ROUTER
        index += 1
