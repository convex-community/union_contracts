import brownie
from tests.utils.merkle import OrderedMerkleTree
from brownie import interface
from tests.utils.constants import (
    AIRFORCE_SAFE,
    UNION_CVX_DISTRIBUTOR,
    PIREX_CVX_VAULT,
)


def test_migration(fn_isolation, alice, owner, cvx_distributor, cvx_vault, migration):
    old_distributor = interface.IGenericDistributor(UNION_CVX_DISTRIBUTOR)
    ucvx = interface.IGenericVault(PIREX_CVX_VAULT)
    old_distributor_ucvx_balance = ucvx.balanceOf(old_distributor)
    new_distributor_initial_ucvx_balance = ucvx.balanceOf(cvx_distributor)
    # Create claim data for migration contract
    merkle_data = [{"user": migration.address, "amount": old_distributor_ucvx_balance}]
    tree = OrderedMerkleTree(merkle_data)
    old_distributor.freeze({"from": AIRFORCE_SAFE})
    old_distributor.updateMerkleRoot(tree.get_root(), True, {"from": AIRFORCE_SAFE})
    proofs = tree.get_proof(migration.address)

    tx = migration.migrate(
        proofs["claim"]["index"],
        migration,
        old_distributor_ucvx_balance,
        proofs["proofs"],
        cvx_distributor,
    )

    assert (
        ucvx.balanceOf(cvx_distributor) - new_distributor_initial_ucvx_balance
        == old_distributor_ucvx_balance
    )
    assert ucvx.balanceOf(cvx_distributor) > 0
