import brownie
from brownie import interface, chain, network
from decimal import Decimal
from ..utils import approx, estimate_output_amount, eth_to_cvxcrv
from ..utils.constants import CLAIM_AMOUNT, TOKENS, CVXCRV_REWARDS, CVXCRV


def test_claim_and_swap(
    fn_isolation,
    owner,
    union_contract,
    set_mock_claims,
    vault,
    claim_tree,
    merkle_distributor_v2,
):
    network.gas_price("0 gwei")
    merkle_distributor_v2.unfreeze({"from": owner})
    proofs = claim_tree.get_proof(union_contract.address)
    params = [
        [token, proofs["claim"]["index"], CLAIM_AMOUNT, proofs["proofs"]]
        for token in TOKENS
    ]

    expected_output_amount, eth_crv_ratio = estimate_output_amount(
        TOKENS, union_contract, 0
    )
    union_contract.setApprovals({"from": owner})
    original_caller_balance = owner.balance()
    tx = union_contract.processIncentives(params, 0, True, False, [0, 0, 0], [10000, 0, 0], {"from": owner})
    distributor_balance = vault.balanceOfUnderlying(merkle_distributor_v2)

    assert merkle_distributor_v2.frozen() == True
    assert distributor_balance == expected_output_amount
