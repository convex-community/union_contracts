import pytest
from brownie import (
    GenericUnionVault,
    interface,
    MockERC20,
    StakingRewards,
    PCvxStrategy,
)
from ....utils.constants import (
    AIRFORCE_SAFE,
)


@pytest.fixture(scope="module")
def pcvx(owner):
    yield MockERC20.deploy("Pirex CVX", "pCVX", owner, 1e25, {"from": owner})


@pytest.fixture(scope="module")
def vault(owner, pcvx, accounts):
    vault = GenericUnionVault.deploy(pcvx, {"from": owner})
    vault.setPlatform(AIRFORCE_SAFE, {"from": owner})
    for account in accounts[:10]:
        pcvx.mint(account, 1e25)
        pcvx.approve(vault, 2**256 - 1, {"from": account})
    yield vault


@pytest.fixture(scope="module")
def staking_rewards(owner, pcvx):
    yield StakingRewards.deploy(pcvx, pcvx, owner, {"from": owner})


@pytest.fixture(scope="module")
def strategy(owner, vault, staking_rewards, pcvx):
    strategy = PCvxStrategy.deploy(vault, staking_rewards, pcvx, {"from": owner})
    strategy.setApprovals({"from": owner})
    vault.setStrategy(strategy, {"from": owner})
    yield strategy
