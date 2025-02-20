import pytest
from brownie import (
    MerkleDistributor,
    MerkleDistributorV2,
    stkCvxFxsMerkleDistributor,
    GenericUnionVault,
    stkCvxFxsVault,
    stkCvxFxsZaps,
    stkCvxPrismaVault,
    stkCvxPrismaZaps,
    StakingRewards,
    GenericDistributor,
    CVXMerkleDistributor,
    PCvxStrategy,
    FXSSwapper,
    PrismaSwapper,
    UnionVault,
    stkCvxFxsStrategy,
    stkCvxPrismaStrategy,
    UnionZap,
    stkCvxCrvMerkleDistributor,
    stkCvxPrismaMerkleDistributor,
    CrvUsdSwapper,
    sCrvUsdDistributor,
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
    UNBALANCED_TOKENS,
    CURVE_TRICRV_POOL,
    CVXFXS,
    CURVE_PRISMA_ETH_POOL,
    CVXPRISMA,
    PRISMA,
    SCRVUSD_VAULT,
    CRVUSD_TOKEN,
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
def crv_distributor(owner, union_contract, vault):
    merkle = stkCvxCrvMerkleDistributor.deploy(
        vault, union_contract, CVXCRV, {"from": owner}
    )
    merkle.setApprovals({"from": owner})
    yield merkle


@pytest.fixture(scope="module")
def fxs_vault(owner):
    vault = stkCvxFxsVault.deploy(CVXFXS, {"from": owner})
    vault.setPlatform(AIRFORCE_SAFE, {"from": owner})
    yield vault


@pytest.fixture(scope="module")
def fxs_strategy(owner, fxs_vault):
    strategy = stkCvxFxsStrategy.deploy(fxs_vault, {"from": owner})
    strategy.setApprovals({"from": owner})
    fxs_vault.setStrategy(strategy, {"from": owner})
    yield strategy


@pytest.fixture(scope="module")
def fxs_zaps(owner, fxs_vault):
    zaps = stkCvxFxsZaps.deploy(fxs_vault, {"from": owner})
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
    fxs_distributor = stkCvxFxsMerkleDistributor.deploy(
        fxs_vault, union_contract, fxs_zaps, {"from": owner}
    )
    fxs_distributor.setApprovals({"from": owner})
    yield fxs_distributor


@pytest.fixture(scope="module")
def prisma_vault(owner):
    vault = stkCvxPrismaVault.deploy(CVXPRISMA, {"from": owner})
    vault.setPlatform(AIRFORCE_SAFE, {"from": owner})
    yield vault


@pytest.fixture(scope="module")
def prisma_strategy(owner, prisma_vault):
    strategy = stkCvxPrismaStrategy.deploy(prisma_vault, {"from": owner})
    strategy.setApprovals({"from": owner})
    prisma_vault.setStrategy(strategy, {"from": owner})
    yield strategy


@pytest.fixture(scope="module")
def prisma_zaps(owner, prisma_vault):
    zaps = stkCvxPrismaZaps.deploy(prisma_vault, {"from": owner})
    zaps.setApprovals({"from": owner})
    yield zaps


@pytest.fixture(scope="module")
def prisma_swapper(owner, union_contract):
    swaps = PrismaSwapper.deploy(union_contract, {"from": owner})
    swaps.setApprovals({"from": owner})
    yield swaps


@pytest.fixture(scope="module")
def prisma_distributor(owner, union_contract, prisma_zaps, prisma_vault):
    prisma_distributor = stkCvxPrismaMerkleDistributor.deploy(
        prisma_vault, union_contract, prisma_zaps, {"from": owner}
    )
    prisma_distributor.setApprovals({"from": owner})
    yield prisma_distributor


@pytest.fixture(scope="module")
def scrvusd_vault(owner):
    yield interface.IERC4626(SCRVUSD_VAULT)


@pytest.fixture(scope="module")
def scrvusd_distributor(owner, union_contract, scrvusd_vault):

    scrvusd_distributor = sCrvUsdDistributor.deploy(
        scrvusd_vault, union_contract, CRVUSD_TOKEN, {"from": owner}
    )
    scrvusd_distributor.setApprovals({"from": owner})
    yield scrvusd_distributor


@pytest.fixture(scope="module")
def crvusd_swapper(owner, union_contract):
    swaps = CrvUsdSwapper.deploy(union_contract, {"from": owner})
    swaps.setApprovals({"from": owner})
    yield swaps


@pytest.fixture(scope="module", autouse=True)
def set_up_ouput_tokens(
    owner,
    vault,
    union_contract,
    crv_distributor,
    fxs_zaps,
    fxs_swapper,
    cvx_vault,
    fxs_vault,
    fxs_strategy,
    fxs_distributor,
    cvx_distributor,
    prisma_zaps,
    prisma_swapper,
    prisma_vault,
    prisma_strategy,
    prisma_distributor,
    crvusd_swapper,
    scrvusd_distributor,
):
    # set up all the output tokens since all contracts are deployed
    union_contract.updateOutputToken(
        CRV, [CURVE_TRICRV_POOL, ADDRESS_ZERO, crv_distributor], {"from": owner}
    )
    union_contract.updateOutputToken(
        CVX, [CURVE_CVX_ETH_POOL, ADDRESS_ZERO, cvx_distributor], {"from": owner}
    )
    union_contract.updateOutputToken(
        FXS, [CURVE_FXS_ETH_POOL, fxs_swapper, fxs_distributor], {"from": owner}
    )
    union_contract.updateOutputToken(
        PRISMA,
        [CURVE_PRISMA_ETH_POOL, prisma_swapper, prisma_distributor],
        {"from": owner},
    )
    union_contract.updateOutputToken(
        CRVUSD_TOKEN,
        [crvusd_swapper, crvusd_swapper, scrvusd_distributor],
        {"from": owner},
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
        VOTIUM_DISTRIBUTOR,
        1e20,
        {"from": "0x8eb8a3b98659cce290402893d0123abb75e3ab28"},  # Avax bridge
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


@pytest.fixture(scope="module")
def set_mock_claims_unbalanced(claim_tree):
    mock_claims(claim_tree, UNBALANCED_TOKENS)
