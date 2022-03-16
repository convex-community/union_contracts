import brownie
from brownie import interface, chain
from ..utils.constants import (
    ADDRESS_ZERO,
    VOTIUM_DISTRIBUTOR,
    CRV,
    CURVE_CRV_ETH_POOL,
    CURVE_CVXCRV_CRV_POOL,
    CVXCRV_DEPOSIT,
    VOTIUM_REGISTRY,
    NSBT,
    CVXCRV_TOKEN,
    CVXCRV_REWARDS,
)


def test_update_distributor(fn_isolation, owner, union_contract):
    tx = union_contract.updateDistributor(VOTIUM_DISTRIBUTOR, {"from": owner})
    assert union_contract.unionDistributor() == VOTIUM_DISTRIBUTOR
    assert len(tx.events) == 1
    assert "DistributorUpdated" in tx.events
    assert tx.events["DistributorUpdated"]["distributor"] == VOTIUM_DISTRIBUTOR


def test_update_distributor_non_owner(alice, union_contract):
    with brownie.reverts("Ownable: caller is not the owner"):
        union_contract.updateDistributor(VOTIUM_DISTRIBUTOR, {"from": alice})


def test_update_distributor_address_zero(owner, union_contract):
    with brownie.reverts():
        union_contract.updateDistributor(ADDRESS_ZERO, {"from": owner})


def test_update_votium_distributor(fn_isolation, owner, union_contract):
    tx = union_contract.updateVotiumDistributor(union_contract, {"from": owner})
    assert union_contract.votiumDistributor() == union_contract
    assert len(tx.events) == 1
    assert "VotiumDistributorUpdated" in tx.events
    assert tx.events["VotiumDistributorUpdated"]["distributor"] == union_contract


def test_update_votium_distributor_non_owner(alice, union_contract):
    with brownie.reverts("Ownable: caller is not the owner"):
        union_contract.updateVotiumDistributor(union_contract, {"from": alice})


def test_update_votium_distributor_address_zero(owner, union_contract):
    with brownie.reverts():
        union_contract.updateVotiumDistributor(ADDRESS_ZERO, {"from": owner})


def test_update_votium_distributor_address_zero(owner, union_contract):
    with brownie.reverts():
        union_contract.updateVotiumDistributor(ADDRESS_ZERO, {"from": owner})


def test_retrieve_tokens(fn_isolation, owner, bob, charlie, union_contract):
    interface.ICurveV2Pool(CURVE_CRV_ETH_POOL).exchange_underlying(
        0, 1, 1e18, 0, {"from": charlie, "value": 1e18}
    )
    crv = interface.IERC20(CRV)
    initial_bob_crv_amount = crv.balanceOf(bob)
    crv_amount = crv.balanceOf(charlie)
    crv.transfer(union_contract, crv_amount, {"from": charlie})
    tx = union_contract.retrieveTokens([CRV], bob, {"from": owner})
    assert initial_bob_crv_amount + crv_amount == crv.balanceOf(bob)
    assert crv.balanceOf(union_contract) == 0
    assert len(tx.events) == 2
    assert "FundsRetrieved" in tx.events
    assert tx.events["FundsRetrieved"]["token"] == CRV
    assert tx.events["FundsRetrieved"]["to"] == bob.address
    assert tx.events["FundsRetrieved"]["amount"] == crv_amount


def test_retrieve_tokens_non_owner(alice, union_contract):
    with brownie.reverts("Ownable: caller is not the owner"):
        union_contract.retrieveTokens([CRV], alice, {"from": alice})


def test_retrieve_tokens_address_zero(owner, union_contract):
    with brownie.reverts():
        union_contract.retrieveTokens([CRV], ADDRESS_ZERO, {"from": owner})


def test_set_approvals(owner, union_contract):
    union_contract.setApprovals({"from": owner})
    crv = interface.IERC20(CRV)
    assert crv.allowance(union_contract, CVXCRV_DEPOSIT) == 2 ** 256 - 1
    assert crv.allowance(union_contract, CURVE_CVXCRV_CRV_POOL) == 2 ** 256 - 1


def test_set_approvals_non_owner(alice, union_contract):
    with brownie.reverts("Ownable: caller is not the owner"):
        union_contract.setApprovals({"from": alice})


def test_set_forwarding(fn_isolation, owner, union_contract):
    assert (
        interface.IVotiumRegistry(VOTIUM_REGISTRY).registry(union_contract.address)[1]
        == ADDRESS_ZERO
    )
    union_contract.setForwarding(VOTIUM_DISTRIBUTOR, {"from": owner})
    assert (
        interface.IVotiumRegistry(VOTIUM_REGISTRY).registry(union_contract.address)[1]
        == VOTIUM_DISTRIBUTOR
    )


def test_set_forwarding_non_owner(alice, union_contract):
    with brownie.reverts("Ownable: caller is not the owner"):
        union_contract.setForwarding(VOTIUM_DISTRIBUTOR, {"from": alice})


def test_execute(fn_isolation, owner, union_contract):
    nsbt_amount = 1e12
    nsbt = interface.IERC20(NSBT)
    nsbt.transfer(
        union_contract,
        nsbt_amount,
        {"from": "0x6871eacd33fbcfe585009ab64f0795d7152dc5a0"},
    )

    previous_balance = nsbt.balanceOf(VOTIUM_REGISTRY)
    calldata = nsbt.transfer.encode_input(VOTIUM_REGISTRY, nsbt_amount)
    union_contract.execute(NSBT, 0, calldata, {"from": owner})
    assert nsbt.balanceOf(union_contract) == 0
    assert nsbt.balanceOf(VOTIUM_REGISTRY) - previous_balance == nsbt_amount


def test_execute_non_owner(alice, union_contract):
    with brownie.reverts("Ownable: caller is not the owner"):
        union_contract.execute(ADDRESS_ZERO, 0, "0x0", {"from": alice})


def test_claim_non_owner(alice, union_contract):
    with brownie.reverts("Ownable: caller is not the owner"):
        union_contract.claim([(ADDRESS_ZERO, 0, 0, ["0x0"])], {"from": alice})


def test_distribute_non_owner(alice, union_contract):
    with brownie.reverts("Ownable: caller is not the owner"):
        union_contract.distribute([], 0, True, True, True, 0, {"from": alice})


def test_add_curve_pool_non_owner(alice, union_contract):
    with brownie.reverts("Ownable: caller is not the owner"):
        union_contract.addCurvePool(NSBT, (NSBT, 0), {"from": alice})


def test_remove_curve_pool_non_owner(fn_isolation, alice, owner, union_contract):
    union_contract.addCurvePool(NSBT, (NSBT, 0), {"from": owner})
    with brownie.reverts("Ownable: caller is not the owner"):
        union_contract.removeCurvePool(NSBT, {"from": alice})


def test_add_curve_pool(fn_isolation, owner, union_contract):
    tx = union_contract.addCurvePool(NSBT, (NSBT, 0), {"from": owner})
    registry_value = union_contract.curveRegistry(NSBT)
    assert registry_value[0] == NSBT
    assert registry_value[1] == 0
    assert tx.events["CurvePoolUpdated"]["token"] == NSBT
    assert tx.events["CurvePoolUpdated"]["pool"] == NSBT

    tx = union_contract.addCurvePool(NSBT, (VOTIUM_REGISTRY, 0), {"from": owner})
    registry_value = union_contract.curveRegistry(NSBT)
    assert registry_value[0] == VOTIUM_REGISTRY
    assert registry_value[1] == 0
    assert tx.events["CurvePoolUpdated"]["token"] == NSBT
    assert tx.events["CurvePoolUpdated"]["pool"] == VOTIUM_REGISTRY


def test_remove_curve_pool(fn_isolation, owner, union_contract):
    union_contract.addCurvePool(NSBT, (NSBT, 0), {"from": owner})
    tx = union_contract.removeCurvePool(NSBT, {"from": owner})
    registry_value = union_contract.curveRegistry(NSBT)
    assert registry_value[0] == ADDRESS_ZERO
    assert registry_value[1] == 0
    assert tx.events["CurvePoolUpdated"]["token"] == NSBT
    assert tx.events["CurvePoolUpdated"]["pool"] == ADDRESS_ZERO

