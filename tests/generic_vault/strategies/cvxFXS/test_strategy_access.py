import brownie
from brownie import chain

from ....utils.constants import AIRFORCE_SAFE, ADDRESS_ZERO


def test_harvest_non_vault(alice, owner, vault, strategy):
    with brownie.reverts("Vault calls only"):
        strategy.harvest(20, 20, ADDRESS_ZERO, AIRFORCE_SAFE, {"from": owner})
    with brownie.reverts("Vault calls only"):
        strategy.harvest(20, 20, ADDRESS_ZERO, AIRFORCE_SAFE, {"from": alice})


def test_withdraw_non_vault(alice, owner, vault, strategy):
    with brownie.reverts("Vault calls only"):
        strategy.withdraw(20, {"from": owner})
    with brownie.reverts("Vault calls only"):
        strategy.withdraw(20, {"from": alice})

