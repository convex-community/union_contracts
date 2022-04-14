import brownie
import pytest
from ..utils.constants import CLAIM_AMOUNT, TOKENS, MAX_UINT256


def test_swap_slippage(
    fn_isolation, owner, union_contract, set_mock_claims, claim_tree, vault
):

    weights = [10000, 0, 0]
    proofs = claim_tree.get_proof(union_contract.address)
    params = [
        [token, proofs["claim"]["index"], CLAIM_AMOUNT, proofs["proofs"]]
        for token in TOKENS
    ]

    with brownie.reverts():
        union_contract.swap(params, 0, True, MAX_UINT256, weights, {"from": owner})


@pytest.mark.parametrize(
    "weights,min_amounts",
    [
        [[10000, 0, 0], [MAX_UINT256, 0, 0]],
        [[0, 10000, 0], [0, MAX_UINT256, 0]],
        [[0, 0, 10000], [0, 0, MAX_UINT256]],
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

    union_contract.swap(params, 0, True, 0, weights, {"from": owner})

    with brownie.reverts():
        union_contract.adjust(lock, weights, min_amounts, {"from": owner})


@pytest.mark.parametrize(
    "weights,min_amounts",
    [
        [[10000, 0, 0], [MAX_UINT256, 0, 0]],
        [[0, 10000, 0], [0, MAX_UINT256, 0]],
        [[0, 0, 10000], [0, 0, MAX_UINT256]],
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
            params, 0, True, lock, weights, min_amounts, {"from": owner}
        )
