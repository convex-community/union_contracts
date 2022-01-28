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


def test_set_union_dues(owner, union_contract):
    tx = union_contract.setUnionDues(350, {"from": owner})
    assert union_contract.unionDues() == 350
    assert len(tx.events) == 1
    assert "DuesUpdated" in tx.events
    assert tx.events["DuesUpdated"]["dues"] == 350
    chain.undo()


def test_set_union_dues_non_owner(alice, union_contract):
    with brownie.reverts("Ownable: caller is not the owner"):
        union_contract.setUnionDues(150, {"from": alice})


def test_set_union_dues_too_high(owner, union_contract):
    with brownie.reverts("Dues too high"):
        union_contract.setUnionDues(2 * 256 - 1, {"from": owner})

    with brownie.reverts("Dues too high"):
        union_contract.setUnionDues(500, {"from": owner})


def test_update_distributor(owner, union_contract):
    tx = union_contract.updateDistributor(VOTIUM_DISTRIBUTOR, {"from": owner})
    assert union_contract.unionDistributor() == VOTIUM_DISTRIBUTOR
    assert len(tx.events) == 1
    assert "DistributorUpdated" in tx.events
    assert tx.events["DistributorUpdated"]["distributor"] == VOTIUM_DISTRIBUTOR
    chain.undo()


def test_update_distributor_non_owner(alice, union_contract):
    with brownie.reverts("Ownable: caller is not the owner"):
        union_contract.updateDistributor(VOTIUM_DISTRIBUTOR, {"from": alice})


def test_update_distributor_address_zero(owner, union_contract):
    with brownie.reverts():
        union_contract.updateDistributor(ADDRESS_ZERO, {"from": owner})


def test_update_votium_distributor(owner, union_contract):
    tx = union_contract.updateVotiumDistributor(union_contract, {"from": owner})
    assert union_contract.votiumDistributor() == union_contract
    assert len(tx.events) == 1
    assert "VotiumDistributorUpdated" in tx.events
    assert tx.events["VotiumDistributorUpdated"]["distributor"] == union_contract
    chain.undo()


def test_update_votium_distributor_non_owner(alice, union_contract):
    with brownie.reverts("Ownable: caller is not the owner"):
        union_contract.updateVotiumDistributor(union_contract, {"from": alice})


def test_update_votium_distributor_address_zero(owner, union_contract):
    with brownie.reverts():
        union_contract.updateVotiumDistributor(ADDRESS_ZERO, {"from": owner})


def test_update_votium_distributor_address_zero(owner, union_contract):
    with brownie.reverts():
        union_contract.updateVotiumDistributor(ADDRESS_ZERO, {"from": owner})


def test_retrieve_tokens(owner, bob, charlie, union_contract):
    chain.snapshot()
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
    chain.revert()


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


def test_set_forwarding(owner, union_contract):
    chain.snapshot()
    assert (
        interface.IVotiumRegistry(VOTIUM_REGISTRY).registry(union_contract.address)[1]
        == ADDRESS_ZERO
    )
    union_contract.setForwarding(VOTIUM_DISTRIBUTOR, {"from": owner})
    assert (
        interface.IVotiumRegistry(VOTIUM_REGISTRY).registry(union_contract.address)[1]
        == VOTIUM_DISTRIBUTOR
    )
    chain.revert()


def test_set_forwarding_non_owner(alice, union_contract):
    with brownie.reverts("Ownable: caller is not the owner"):
        union_contract.setForwarding(VOTIUM_DISTRIBUTOR, {"from": alice})


def test_execute(owner, union_contract):
    chain.snapshot()
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
    chain.revert()


def test_execute_non_owner(alice, union_contract):
    with brownie.reverts("Ownable: caller is not the owner"):
        union_contract.execute(ADDRESS_ZERO, 0, "0x0", {"from": alice})


def test_claim_non_owner(alice, union_contract):
    with brownie.reverts("Ownable: caller is not the owner"):
        union_contract.claim([(ADDRESS_ZERO, 0, 0, ["0x0"])], {"from": alice})


def test_stake_non_owner(alice, union_contract):
    with brownie.reverts("Ownable: caller is not the owner"):
        union_contract.stakeAccumulated({"from": alice})


def test_stake(owner, union_contract):
    chain.snapshot()
    initial_balance = interface.IERC20(CVXCRV_TOKEN).balanceOf(owner)
    amount = 1234567890
    interface.IERC20(CVXCRV_TOKEN).transfer(
        union_contract, amount, {"from": CURVE_CVXCRV_CRV_POOL}
    )
    union_contract.stakeAccumulated({"from": owner})
    assert interface.IBasicRewards(CVXCRV_REWARDS).balanceOf(owner) == amount - 1
    interface.IBasicRewards(CVXCRV_REWARDS).withdrawAll(False, {"from": owner})
    assert (
        interface.IERC20(CVXCRV_TOKEN).balanceOf(owner) - initial_balance == amount - 1
    )
    chain.revert()


def test_claim_accumulated(owner, bob, union_contract):
    chain.snapshot()
    bob_initial_balance = interface.IERC20(CVXCRV_TOKEN).balanceOf(bob)
    amount = 1234567890
    interface.IERC20(CVXCRV_TOKEN).transfer(
        union_contract, amount, {"from": CURVE_CVXCRV_CRV_POOL}
    )
    union_contract.claimAccumulated(amount, bob, {"from": owner})
    assert interface.IERC20(CVXCRV_TOKEN).balanceOf(bob) - bob_initial_balance == amount
    chain.revert()


def test_claim_accumulated_non_owner(alice, union_contract):
    with brownie.reverts("Ownable: caller is not the owner"):
        union_contract.claimAccumulated(12345, alice, {"from": alice})


def test_claim_accumulated_to_zero_address(owner, union_contract):
    with brownie.reverts():
        union_contract.claimAccumulated(12345, ADDRESS_ZERO, {"from": owner})


def test_distribute_non_owner(alice, union_contract):
    with brownie.reverts("Ownable: caller is not the owner"):
        union_contract.distribute([], 0, True, True, True, 0, {"from": alice})
