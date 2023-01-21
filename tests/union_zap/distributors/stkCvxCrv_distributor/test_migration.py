import brownie

from tests.utils.merkle import OrderedMerkleTree
from brownie import interface
from tests.utils.constants import (
    CLAIM_AMOUNT,
    CVX, CURVE_CVXCRV_CRV_POOL, FXS, UNION_CRV, AIRFORCE_SAFE, UNION_CRV_DISTRIBUTOR,
)
from tests.utils import approx, get_crv_to_eth_amount, eth_to_crv, cvxcrv_to_crv, eth_to_cvx


def test_migration(
    fn_isolation,
    alice,
    owner,
    distributor,
    vault,
    migration
):
    old_distributor = interface.IGenericDistributor(UNION_CRV_DISTRIBUTOR)
    old_distributor_cvxcrv_balance = interface.IGenericVault(UNION_CRV).balanceOfUnderlying(old_distributor)
    old_distributor_ucrv_balance = interface.IERC20(UNION_CRV).balanceOf(old_distributor)
    original_distributor_cvxcrv_balance = vault.balanceOfUnderlying(distributor)
    # Create claim data for migration contract
    merkle_data = [{"user": migration.address, "amount": old_distributor_ucrv_balance}]
    tree = OrderedMerkleTree(merkle_data)
    old_distributor.freeze({"from": AIRFORCE_SAFE})
    old_distributor.updateMerkleRoot(tree.get_root(), True, {"from": AIRFORCE_SAFE})
    proofs = tree.get_proof(migration.address)

    migration.migrate(proofs["claim"]["index"],
                      migration,
                      old_distributor_ucrv_balance,
                      proofs["proofs"],
                      vault,
                      distributor
                      )

    assert vault.balanceOfUnderlying(distributor) - original_distributor_cvxcrv_balance == old_distributor_cvxcrv_balance
