import pytest
import brownie
from brownie import interface
from tests.utils.constants import (
    CVXCRV,
)

from tests.utils.constants import CVXCRV_REWARDS


@pytest.fixture(scope="module", autouse=True)
def distribute_cvx_crv(merkle_distributor):
    interface.IERC20(CVXCRV).transfer(
        merkle_distributor, 1e25, {"from": CVXCRV_REWARDS}
    )
