import pytest
from brownie import chain

from ....utils.constants import CVXCRV_REWARDS


def test_asset_switch(wrapper, alice, bob, charlie, dave):
    wrapper.setRewardWeight(5000, {"from": alice})
    wrapper.setRewardWeight(5000, {"from": bob})
    wrapper.setRewardWeight(5000, {"from": charlie})
    wrapper.setRewardWeight(5000, {"from": dave})
    wrapper.stake(1e23, alice, {"from": alice})
    wrapper.stake(1e23, bob, {"from": bob})
    wrapper.stake(1e23, charlie, {"from": charlie})
    wrapper.stake(1e23, dave, {"from": dave})
    chain.sleep(60 * 60 * 24 * 2)
    chain.mine(1)
    for account in [alice, bob, charlie, dave]:
        res = wrapper.earned(account).return_value
        for pair in res:
            token, qtty = pair
            print(token[:8] + ":" + str(qtty * 1e-18))
        chain.undo(1)
        print("-" * 30)

    print("\n")
    print("=" * 30)
    wrapper.setRewardWeight(0, {"from": dave})
    wrapper.setRewardWeight(10000, {"from": charlie})
    chain.sleep(60 * 60 * 24 * 2)
    chain.mine(1)
    for account in [alice, bob, charlie, dave]:
        res = wrapper.earned(account).return_value
        for pair in res:
            token, qtty = pair
            print(token[:8] + ":" + str(qtty * 1e-18))
        chain.undo(1)
        print("=" * 30)
