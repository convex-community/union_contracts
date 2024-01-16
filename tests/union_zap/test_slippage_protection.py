import brownie
import pytest
from ..utils.constants import CLAIM_AMOUNT, TOKENS, MAX_UINT256, MAX_WEIGHT_1E9


def test_swap_slippage(
    fn_isolation, owner, union_contract, set_mock_claims, claim_tree, vault
):

    weights = [MAX_WEIGHT_1E9, 0, 0, 0]
    proofs = claim_tree.get_proof(union_contract.address)
    params = [
        [token, proofs["claim"]["index"], CLAIM_AMOUNT, proofs["proofs"]]
        for token in TOKENS
    ]

    with brownie.reverts():
        union_contract.swap(params, 0, True, MAX_UINT256, 0, weights, {"from": owner})


@pytest.mark.parametrize(
    "weights,min_amounts",
    [
        [[0, 0, 0, MAX_WEIGHT_1E9], [0, 0, 0, MAX_UINT256 // 2]],
        [[MAX_WEIGHT_1E9, 0, 0, 0], [MAX_UINT256, 0, 0, 0]],
        [[0, MAX_WEIGHT_1E9, 0, 0], [0, MAX_UINT256, 0, 0]],
        [[0, 0, MAX_WEIGHT_1E9, 0], [0, 0, MAX_UINT256, 0]],
    ],
)
@pytest.mark.parametrize("lock", [True, False])
def test_adjust_slippage(
    fn_isolation,
    owner,
    union_contract,
    set_mock_claims,
    claim_tree,
    lock,
    weights,
    min_amounts,
    vault,
):

    proofs = claim_tree.get_proof(union_contract.address)
    params = [
        [token, proofs["claim"]["index"], CLAIM_AMOUNT, proofs["proofs"]]
        for token in TOKENS
    ]

    union_contract.swap(params, 0, True, 0, 0, weights, {"from": owner})

    with brownie.reverts():
        union_contract.adjust(lock, weights, [0, 1, 2, 3], min_amounts, {"from": owner})


@pytest.mark.parametrize(
    "weights,min_amounts",
    [
        [[0, 0, 0, MAX_WEIGHT_1E9], [0, 0, 0, MAX_UINT256]],
        [[MAX_WEIGHT_1E9, 0, 0], [MAX_UINT256, 0, 0]],
        [[0, MAX_WEIGHT_1E9, 0], [0, MAX_UINT256, 0]],
        [[0, 0, MAX_WEIGHT_1E9], [0, 0, MAX_UINT256]],
    ],
)
@pytest.mark.parametrize("lock", [True, False])
def test_process_incentives_slippage(
    fn_isolation,
    owner,
    union_contract,
    set_mock_claims,
    claim_tree,
    lock,
    weights,
    min_amounts,
    vault,
):

    proofs = claim_tree.get_proof(union_contract.address)
    params = [
        [token, proofs["claim"]["index"], CLAIM_AMOUNT, proofs["proofs"]]
        for token in TOKENS
    ]

    with brownie.reverts():
        union_contract.processIncentives(
            params,
            0,
            True,
            lock,
            0,
            weights,
            [0, 1, 2, 3],
            min_amounts,
            {"from": owner},
        )
