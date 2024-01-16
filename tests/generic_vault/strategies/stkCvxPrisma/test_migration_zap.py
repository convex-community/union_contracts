from brownie import interface
from tests.utils.constants import C2TP_WALLET, CVXPRISMA_STAKING_CONTRACT


def test_migration(fn_isolation, alice, owner, vault, strategy, staking, migration):
    alice_initial_shares = vault.balanceOf(alice)
    initial_underlying = vault.totalUnderlying()
    c2_initial_staking = staking.balanceOf(C2TP_WALLET)
    strategy_initial_staking = staking.balanceOf(strategy)

    interface.IERC20(CVXPRISMA_STAKING_CONTRACT).approve(
        migration, 2**256 - 1, {"from": C2TP_WALLET}
    )
    tx = migration.migrate(c2_initial_staking, alice, {"from": C2TP_WALLET})

    assert vault.balanceOf(alice) == alice_initial_shares + c2_initial_staking
    assert vault.totalUnderlying() == initial_underlying + c2_initial_staking
    assert staking.balanceOf(C2TP_WALLET) == 0
    assert staking.balanceOf(strategy) == strategy_initial_staking + c2_initial_staking
