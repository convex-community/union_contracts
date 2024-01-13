import brownie
from brownie import chain, interface

from ....utils.constants import (
    PRISMA,
    CRV_TOKEN,
    CVX,
    MKUSD_TOKEN,
    CURVE_CVXCRV_CRV_POOL_V2,
)

# HARVESTER ACCESS TESTS


def test_harvester_set_force_lock_non_owner(fn_isolation, alice, owner, harvester):
    with brownie.reverts("owner only"):
        harvester.setForceLock({"from": alice})


def test_harvester_rescue_tokens_access(fn_isolation, alice, harvester):
    with brownie.reverts("owner only"):
        harvester.rescueToken(PRISMA, alice, {"from": alice})


def test_harvester_rescue_reward_tokens(fn_isolation, owner, harvester):
    with brownie.reverts("not allowed"):
        harvester.rescueToken(PRISMA, owner, {"from": owner})
    with brownie.reverts("not allowed"):
        harvester.rescueToken(CVX, owner, {"from": owner})
    with brownie.reverts("not allowed"):
        harvester.rescueToken(MKUSD_TOKEN, owner, {"from": owner})


def test_harvester_rescue_tokens(fn_isolation, owner, vault, harvester):
    original_owner_balance = interface.IERC20(CRV_TOKEN).balanceOf(owner)
    interface.IERC20(CRV_TOKEN).transfer(
        harvester, 1e24, {"from": CURVE_CVXCRV_CRV_POOL_V2}
    )
    harvester.rescueToken(CRV_TOKEN, owner, {"from": owner})
    assert interface.IERC20(CRV_TOKEN).balanceOf(owner) > original_owner_balance


def test_harvester_set_slippage(fn_isolation, alice, owner, harvester):
    with brownie.reverts("owner only"):
        harvester.setSlippage(9500, {"from": alice})
    harvester.setSlippage(1000, {"from": owner})
    assert harvester.allowedSlippage() == 1000


def test_harvester_switch_oracle(fn_isolation, alice, owner, harvester):
    with brownie.reverts("owner only"):
        harvester.switchOracle({"from": alice})
    use_oracle = harvester.useOracle()
    harvester.switchOracle({"from": owner})
    assert use_oracle != harvester.useOracle()


def test_harvester_set_force_lock(fn_isolation, owner, harvester):
    assert harvester.forceLock() == False
    harvester.setForceLock({"from": owner})
    assert harvester.forceLock() == True
    harvester.setForceLock({"from": owner})
    assert harvester.forceLock() == False


def test_harvester_set_pending_owner(fn_isolation, alice, harvester):
    with brownie.reverts("owner only"):
        harvester.setPendingOwner(alice, {"from": alice})


def test_accept_pending_owner(fn_isolation, alice, bob, owner, harvester):
    with brownie.reverts("only new owner"):
        harvester.acceptOwnership({"from": owner})
    harvester.setPendingOwner(alice, {"from": owner})
    with brownie.reverts("only new owner"):
        harvester.acceptOwnership({"from": owner})
    with brownie.reverts("only new owner"):
        harvester.acceptOwnership({"from": bob})
    harvester.setPendingOwner(alice, {"from": owner})
    harvester.acceptOwnership({"from": alice})
    with brownie.reverts("owner only"):
        harvester.setPendingOwner(alice, {"from": owner})
    harvester.setPendingOwner(owner, {"from": alice})
    harvester.acceptOwnership({"from": owner})
    assert harvester.owner() == owner


def test_process_rewards(fn_isolation, alice, harvester):
    with brownie.reverts("strategy only"):
        harvester.processRewards({"from": alice})
