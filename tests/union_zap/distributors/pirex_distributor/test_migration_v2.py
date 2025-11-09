import brownie
from tests.utils.merkle import OrderedMerkleTree
from brownie import interface
from tests.utils.constants import (
    AIRFORCE_SAFE,
    UNION_CVX_DISTRIBUTOR_2,
    PIREX_CVX_VAULT,
)


def test_migration(fn_isolation, alice, owner, cvx_distributor, cvx_vault, migration_v2):
    old_distributor = interface.IGenericDistributor(UNION_CVX_DISTRIBUTOR_2)
    ucvx = interface.IGenericVault(PIREX_CVX_VAULT)
    old_distributor_ucvx_balance = ucvx.balanceOf(old_distributor)
    new_distributor_initial_ucvx_balance = ucvx.balanceOf(cvx_distributor)
    # Create claim data for migration contract
    merkle_data = [{"user": migration_v2.address, "amount": old_distributor_ucvx_balance}]
    tree = OrderedMerkleTree(merkle_data)
    old_distributor.freeze({"from": AIRFORCE_SAFE})
    old_distributor.updateMerkleRoot(tree.get_root(), True, {"from": AIRFORCE_SAFE})
    proofs = tree.get_proof(migration_v2.address)

    tx = migration_v2.migrate(
        proofs["claim"]["index"],
        migration_v2,
        old_distributor_ucvx_balance,
        proofs["proofs"],
        cvx_distributor,
    )

    assert (
        ucvx.balanceOf(cvx_distributor) - new_distributor_initial_ucvx_balance
        == old_distributor_ucvx_balance
    )
    assert ucvx.balanceOf(cvx_distributor) > 0
