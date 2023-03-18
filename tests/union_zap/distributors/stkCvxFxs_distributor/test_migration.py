import brownie

from tests.utils.cvxfxs import estimate_underlying_received
from tests.utils.merkle import OrderedMerkleTree
from brownie import interface
from tests.utils.constants import (
    CLAIM_AMOUNT,
    CVX,
    CURVE_CVXCRV_CRV_POOL,
    FXS,
    UNION_FXS,
    AIRFORCE_SAFE,
    UNION_FXS_DISTRIBUTOR,
    CVXFXS,
)
from tests.utils import (
    approx,
    get_crv_to_eth_amount,
    eth_to_crv,
    cvxcrv_to_crv,
    eth_to_cvx,
)


def test_migration(fn_isolation, alice, owner, fxs_distributor, fxs_vault, migration):
    interface.IGenericVault(UNION_FXS).setWithdrawalPenalty(0, {"from": AIRFORCE_SAFE})
    old_distributor = interface.IGenericDistributor(UNION_FXS_DISTRIBUTOR)
    old_distributor_cvxfxs_lp_balance = interface.IGenericVault(
        UNION_FXS
    ).balanceOfUnderlying(old_distributor)
    old_distributor_cvxfxs_balance = estimate_underlying_received(
        old_distributor_cvxfxs_lp_balance, 1
    )
    old_distributor_ufxs_balance = interface.IERC20(UNION_FXS).balanceOf(
        old_distributor
    )
    new_distributor_initial_cvxfxs_balance = fxs_vault.balanceOfUnderlying(
        fxs_distributor
    )
    # Create claim data for migration contract
    merkle_data = [{"user": migration.address, "amount": old_distributor_ufxs_balance}]
    tree = OrderedMerkleTree(merkle_data)
    old_distributor.freeze({"from": AIRFORCE_SAFE})
    old_distributor.updateMerkleRoot(tree.get_root(), True, {"from": AIRFORCE_SAFE})
    proofs = tree.get_proof(migration.address)

    tx = migration.migrate(
        proofs["claim"]["index"],
        migration,
        old_distributor_ufxs_balance,
        proofs["proofs"],
        fxs_vault,
        fxs_distributor,
        0,
    )

    assert (
        fxs_vault.balanceOfUnderlying(fxs_distributor)
        - new_distributor_initial_cvxfxs_balance
        == old_distributor_cvxfxs_balance
    )
    assert fxs_vault.balanceOf(fxs_distributor) > 0
