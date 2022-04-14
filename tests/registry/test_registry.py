import brownie
import random


def test_record_allocation(alice, registry):
    choice = [random.randint(0, 10000) for _ in range(16)]
    registry.recordAllocation(choice, {"from": alice})
    for i, weight in enumerate(choice):
        assert registry.assetAllocations(alice, i) == weight


def test_get_allocations(alice, bob, charlie, dave, registry):
    choices = []
    users = [alice, bob, charlie, dave]
    for user in users:
        choice = [random.randint(0, 10000) for _ in range(16)]
        choices.append(choice)
        registry.recordAllocation(choice, {"from": user})
    assert registry.getAllocations([user.address for user in users]) == choices
