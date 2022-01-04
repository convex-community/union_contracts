import pytest
import brownie
from brownie import interface
from ...utils.constants import (
    CVXCRV,
)

from ...utils.constants import CVXCRV_REWARDS


@pytest.fixture(scope="module", autouse=True)
def distribute_cvx_crv(merkle_distributor_v2):
    interface.IERC20(CVXCRV).transfer(
        merkle_distributor_v2, 1e25, {"from": CVXCRV_REWARDS}
    )
    merkle_distributor_v2.stake()
