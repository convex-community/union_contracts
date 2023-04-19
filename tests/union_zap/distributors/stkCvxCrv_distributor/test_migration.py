import brownie

from tests.utils import approx
from tests.utils.merkle import OrderedMerkleTree
from brownie import interface
from tests.utils.constants import (
    UNION_CRV_V2,
    AIRFORCE_SAFE,
    UNION_CRV_DISTRIBUTOR_V2,
)


def test_migration(fn_isolation, alice, owner, distributor, vault, migration):
    old_distributor = interface.IGenericDistributor(UNION_CRV_DISTRIBUTOR_V2)
    old_distributor_cvxcrv_balance = interface.IGenericVault(
        UNION_CRV_V2
    ).balanceOfUnderlying(old_distributor)
    old_distributor_ucrv_balance = interface.IERC20(UNION_CRV_V2).balanceOf(
        old_distributor
    )
    original_distributor_cvxcrv_balance = vault.balanceOfUnderlying(distributor)
    interface.IGenericVault(UNION_CRV_V2).setWithdrawalPenalty(
        0, {"from": AIRFORCE_SAFE}
    )
    # Create claim data for migration contract
    merkle_data = [{"user": migration.address, "amount": old_distributor_ucrv_balance}]
    tree = OrderedMerkleTree(merkle_data)
    old_distributor.freeze({"from": AIRFORCE_SAFE})
    old_distributor.updateMerkleRoot(tree.get_root(), True, {"from": AIRFORCE_SAFE})
    proofs = tree.get_proof(migration.address)

    tx = migration.migrate(
        proofs["claim"]["index"],
        migration,
        old_distributor_ucrv_balance,
        proofs["proofs"],
        vault,
        distributor,
    )

    assert approx(
        vault.balanceOfUnderlying(distributor) - original_distributor_cvxcrv_balance,
        old_distributor_cvxcrv_balance,
        1e-12,
    )
    assert vault.balanceOf(distributor) > 0
