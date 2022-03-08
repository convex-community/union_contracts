import brownie
from brownie import chain

from ....utils.constants import AIRFORCE_SAFE, ADDRESS_ZERO


def test_set_swap_option_non_owner(alice, vault, strategy):
    with brownie.reverts("Ownable: caller is not the owner"):
        strategy.setSwapOption(0, {"from": alice})


def test_set_swap_option(fn_isolation, owner, vault, strategy):
    for i in range(3):
        tx = strategy.setSwapOption(i, {"from": owner})
        assert strategy.swapOption() == i
        assert tx.events["OptionChanged"]["newOption"] == i

    with brownie.reverts():
        strategy.setSwapOption(4, {"from": owner})
