import brownie
from brownie import chain

from ....utils.constants import AIRFORCE_SAFE


def test_harvest_non_vault(alice, owner, vault, strategy):
    with brownie.reverts("Vault calls only"):
        strategy.harvest(AIRFORCE_SAFE, {"from": owner})
    with brownie.reverts("Vault calls only"):
        strategy.harvest(AIRFORCE_SAFE, {"from": alice})


def test_withdraw_non_vault(alice, owner, vault, strategy):
    with brownie.reverts("Vault calls only"):
        strategy.withdraw(20, {"from": owner})
    with brownie.reverts("Vault calls only"):
        strategy.withdraw(20, {"from": alice})
