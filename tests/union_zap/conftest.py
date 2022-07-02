import pytest
from brownie import (
    MerkleDistributor,
    MerkleDistributorV2,
    FXSMerkleDistributor,
    GenericUnionVault,
    CvxFxsStrategy,
    CvxFxsZaps,
    StakingRewards,
    GenericDistributor,
    CVXMerkleDistributor,
    PCvxStrategy,
    FXSSwapper,
    UnionVault,
    UnionZap,
    interface,
)
from ..utils.constants import (
    TOKENS,
    CLAIM_AMOUNT,
    VOTIUM_DISTRIBUTOR,
    VOTIUM_OWNER,
    CVXCRV,
    AIRFORCE_SAFE,
    CURVE_CVXFXS_FXS_LP_TOKEN,
    ADDRESS_ZERO,
    WETH,
    REGULAR_TOKENS,
    V3_TOKENS,
    V3_1_TOKENS,
    CURVE_TOKENS,
    CVX,
    CURVE_CRV_ETH_POOL,
    CURVE_CVX_ETH_POOL,
    CRV,
    FXS,
    CURVE_FXS_ETH_POOL,
    PIREX_CVX_VAULT,
    PIREX_CVX,
)
from ..utils.merkle import OrderedMerkleTree


@pytest.fixture(scope="session")
def alice(accounts):
    yield accounts[1]


@pytest.fixture(scope="session")
def bob(accounts):
    yield accounts[2]


@pytest.fixture(scope="session")
def charlie(accounts):
    yield accounts[3]


@pytest.fixture(scope="session")
def dave(accounts):
    yield accounts[4]


@pytest.fixture(scope="session")
def erin(accounts):
    yield accounts[5]


@pytest.fixture(scope="session")
def owner(accounts):
    yield accounts[0]


@pytest.fixture(scope="module")
def union_contract(owner):
    union_contract = UnionZap.deploy({"from": owner})
    union_contract.setApprovals({"from": owner})
    yield union_contract


@pytest.fixture(scope="module")
def merkle_distributor(owner, union_contract):
    merkle = MerkleDistributor.deploy(CVXCRV, union_contract, "0x0", {"from": owner})
    yield merkle


@pytest.fixture(scope="module")
def vault(owner):
    vault = UnionVault.deploy({"from": owner})
    vault.setApprovals({"from": owner})
    yield vault


@pytest.fixture(scope="module")
def merkle_distributor_v2(owner, union_contract, vault):
    merkle = MerkleDistributorV2.deploy(vault, union_contract, {"from": owner})
    merkle.setApprovals({"from": owner})
    yield merkle


@pytest.fixture(scope="module")
def fxs_vault(owner):
    vault = GenericUnionVault.deploy(CURVE_CVXFXS_FXS_LP_TOKEN, {"from": owner})
    vault.setPlatform(AIRFORCE_SAFE, {"from": owner})
    yield vault


@pytest.fixture(scope="module")
def fxs_strategy(owner, fxs_vault):
    strategy = CvxFxsStrategy.deploy(fxs_vault, {"from": owner})
    strategy.setApprovals({"from": owner})
    fxs_vault.setStrategy(strategy, {"from": owner})
    yield strategy


@pytest.fixture(scope="module")
def fxs_zaps(owner, fxs_vault):
    zaps = CvxFxsZaps.deploy(fxs_vault, {"from": owner})
    zaps.setApprovals({"from": owner})
    yield zaps


@pytest.fixture(scope="module")
def fxs_swapper(owner, union_contract):
    swaps = FXSSwapper.deploy(union_contract, {"from": owner})
    swaps.setApprovals({"from": owner})
    yield swaps


@pytest.fixture(scope="module")
def cvx_vault(owner):
    vault = interface.IERC4626(PIREX_CVX_VAULT)
    yield vault


@pytest.fixture(scope="module")
def pirex_cvx(owner):
    pcvx = interface.IPirexCVX(PIREX_CVX)
    yield pcvx


@pytest.fixture(scope="module")
def cvx_distributor(owner, cvx_vault, pirex_cvx, union_contract):
    merkle = CVXMerkleDistributor.deploy(
        cvx_vault, union_contract, CVX, {"from": owner}
    )
    merkle.setApprovals({"from": owner})
    yield merkle


@pytest.fixture(scope="module")
def fxs_distributor(owner, union_contract, fxs_zaps, fxs_vault):
    fxs_distributor = FXSMerkleDistributor.deploy(
        fxs_vault, union_contract, fxs_zaps, {"from": owner}
    )
    fxs_distributor.setApprovals({"from": owner})
    yield fxs_distributor


@pytest.fixture(scope="module", autouse=True)
def set_up_ouput_tokens(
    owner,
    vault,
    union_contract,
    merkle_distributor_v2,
    fxs_zaps,
    fxs_swapper,
    cvx_vault,
    fxs_vault,
    fxs_strategy,
    fxs_distributor,
    cvx_distributor,
):
    # set up all the output tokens since all contracts are deployed
    union_contract.updateOutputToken(
        CRV, [CURVE_CRV_ETH_POOL, ADDRESS_ZERO, merkle_distributor_v2], {"from": owner}
    )
    union_contract.updateOutputToken(
        CVX, [CURVE_CVX_ETH_POOL, ADDRESS_ZERO, cvx_distributor], {"from": owner}
    )
    union_contract.updateOutputToken(
        FXS, [CURVE_FXS_ETH_POOL, fxs_swapper, fxs_distributor], {"from": owner}
    )


@pytest.fixture(scope="module")
def claim_tree(accounts, union_contract):
    claimers = [acc.address for acc in accounts[4:9]] + [union_contract.address]
    data = [{"user": claimer, "amount": CLAIM_AMOUNT} for claimer in claimers]
    tree = OrderedMerkleTree(data)
    return tree


def mock_claims(claim_tree, token_list):
    votium_multi_merkle = interface.IMultiMerkleStash(VOTIUM_DISTRIBUTOR)
    interface.IERC20(WETH).transfer(
        VOTIUM_DISTRIBUTOR, 1e20, {"from": "0xe78388b4ce79068e89bf8aa7f218ef6b9ab0e9d0"}
    )
    for token in token_list:
        votium_multi_merkle.updateMerkleRoot(
            token, claim_tree.get_root(), {"from": VOTIUM_OWNER}
        )


@pytest.fixture(scope="module")
def set_mock_claims(claim_tree):
    mock_claims(claim_tree, TOKENS)


@pytest.fixture(scope="module")
def set_mock_claims_regular(claim_tree):
    mock_claims(claim_tree, REGULAR_TOKENS)


@pytest.fixture(scope="module")
def set_mock_claims_v3(claim_tree):
    mock_claims(claim_tree, V3_TOKENS)


@pytest.fixture(scope="module")
def set_mock_claims_v3_1(claim_tree):
    mock_claims(claim_tree, V3_1_TOKENS)


@pytest.fixture(scope="module")
def set_mock_claims_curve(claim_tree):
    mock_claims(claim_tree, CURVE_TOKENS + V3_1_TOKENS)
