import brownie
import random
from decimal import Decimal
from brownie import interface, chain, network
from ..utils import approx, estimate_output_amount
from ..utils.constants import (
    CLAIM_AMOUNT,
    REGULAR_TOKENS,
    CVXCRV,
    UNI_ROUTER,
    SUSHI_ROUTER,
    CVXCRV_REWARDS,
)


def test_claim_and_swap_on_uniswap(
    fn_isolation,
    owner,
    union_contract,
    set_mock_claims_regular,
    claim_tree,
    merkle_distributor_v2,
    vault,
):
    network.gas_price("0 gwei")
    original_union_balance = interface.IERC20(CVXCRV).balanceOf(union_contract)
    merkle_distributor_v2.unfreeze({"from": owner})
    proofs = claim_tree.get_proof(union_contract.address)
    params = [
        [token, proofs["claim"]["index"], CLAIM_AMOUNT, proofs["proofs"]]
        for token in REGULAR_TOKENS
    ]

    expected_output_amount, eth_crv_ratio = estimate_output_amount(
        REGULAR_TOKENS, union_contract, (8 ** (1 + len(params)) - 1) // 7
    )
    union_contract.setApprovals({"from": owner})
    tx = union_contract.distribute(
        params, (8 ** (1 + len(params)) - 1) // 7, True, False, True, 0, {"from": owner}
    )
    distributor_balance = vault.balanceOfUnderlying(merkle_distributor_v2)
    union_balance = interface.IERC20(CVXCRV).balanceOf(union_contract)
    assert distributor_balance > 0
    assert union_balance == original_union_balance
    assert merkle_distributor_v2.frozen() == True
    gas_fees_in_crv = tx.events["Distributed"]["fees"]
    assert distributor_balance == expected_output_amount - gas_fees_in_crv

    for approval in tx.events["Approval"]:
        guy = "guy" if "guy" in approval else "spender"
        if approval[guy] in [vault, CVXCRV_REWARDS]:
            continue
        assert approval[guy] == UNI_ROUTER


def test_claim_and_swap_on_uniswap_and_sushi(
    fn_isolation,
    owner,
    union_contract,
    set_mock_claims_regular,
    claim_tree,
    merkle_distributor_v2,
    vault,
):
    network.gas_price("0 gwei")
    original_union_balance = interface.IERC20(CVXCRV).balanceOf(union_contract)
    merkle_distributor_v2.unfreeze({"from": owner})
    proofs = claim_tree.get_proof(union_contract.address)
    params = [
        [token, proofs["claim"]["index"], CLAIM_AMOUNT, proofs["proofs"]]
        for token in REGULAR_TOKENS
    ]
    routers = [random.randint(0, 1) for _ in REGULAR_TOKENS]
    router_choices = sum([8 ** i * routers[i] for i, _ in enumerate(routers)])
    print(f"ROUTER CHOICES: {router_choices} ({routers})")
    expected_output_amount, eth_crv_ratio = estimate_output_amount(
        REGULAR_TOKENS, union_contract, router_choices
    )
    union_contract.setApprovals({"from": owner})
    tx = union_contract.distribute(
        params, router_choices, True, False, True, 0, {"from": owner}
    )
    distributor_balance = vault.balanceOfUnderlying(merkle_distributor_v2)
    union_balance = interface.IERC20(CVXCRV).balanceOf(union_contract)

    assert distributor_balance > 0
    assert union_balance == original_union_balance
    assert merkle_distributor_v2.frozen() == True

    index = 0
    for approval in tx.events["Approval"]:
        wad = "wad" if "wad" in approval else "value"
        guy = "guy" if "guy" in approval else "spender"
        if approval[guy] in [vault, CVXCRV_REWARDS]:
            continue
        if approval[wad] != CLAIM_AMOUNT - 1:
            continue
        if routers[index] == 1:
            assert approval[guy] == UNI_ROUTER
        else:
            assert approval[guy] == SUSHI_ROUTER
        index += 1

    gas_fees_in_crv = tx.events["Distributed"]["fees"]
    assert distributor_balance == expected_output_amount - gas_fees_in_crv
