// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "../../../interfaces/ICurveV2Pool.sol";
import "../../../interfaces/ICurvePool.sol";
import "../../../interfaces/ICurveFactoryPool.sol";
import "../../../interfaces/IBasicRewards.sol";
import "../../../interfaces/IWETH.sol";

interface ICvxPrismaDeposit {
    function deposit(uint256, bool) external;
}

contract stkCvxPrismaStrategyBase {
    address public constant PRISMA_DEPOSIT =
        0x61404F7c2d8b1F3373eb3c6e8C4b8d8332c2D5B8;

    address public constant CURVE_CVX_ETH_POOL =
        0xB576491F1E6e5E62f1d8F26062Ee822B40B0E0d4;
    address public constant CURVE_PRISMA_ETH_POOL =
        0x322135Dd9cBAE8Afa84727d9aE1434b5B3EBA44B;

    address public constant CURVE_CVXPRISMA_PRISMA_POOL =
        0x3b21C2868B6028CfB38Ff86127eF22E68d16d53B;
    address public constant CURVE_PRISMA_MKUSD_POOL =
        0x9D8108DDD8aD1Ee89d527C0C9e928Cb9D2BBa2d3;

    address public constant CVXPRISMA_TOKEN =
        0x34635280737b5BFe6c7DC2FC3065D60d66e78185;
    address public constant PRISMA_TOKEN =
        0xdA47862a83dac0c112BA89c6abC2159b95afd71C;
    address public constant CVX_TOKEN =
        0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B;
    address public constant MKUSD_TOKEN =
        0x4591DBfF62656E7859Afe5e45f6f47D3669fBB28;

    uint256 public constant PRISMAETH_ETH_INDEX = 0;
    uint256 public constant PRISMAETH_PRISMA_INDEX = 1;
    uint256 public constant CVXETH_ETH_INDEX = 0;
    uint256 public constant CVXETH_CVX_INDEX = 1;
    uint256 public constant PRISMAMKUSD_MKUSD_INDEX = 0;
    uint256 public constant PRISMAMKUSD_PRISMA_INDEX = 1;
    uint256 public constant PRISMACVXPRISMA_CVXPRISMA_INDEX = 1;
    uint256 public constant PRISMACVXPRISMA_PRISMA_INDEX = 0;

    ICvxPrismaDeposit cvxPrismaDeposit = ICvxPrismaDeposit(PRISMA_DEPOSIT);
    ICurveV2Pool cvxEthSwap = ICurveV2Pool(CURVE_CVX_ETH_POOL);
    ICurveV2Pool prismaEthSwap = ICurveV2Pool(CURVE_PRISMA_ETH_POOL);
    ICurveV2Pool cvxPrismaPrismaSwap =
        ICurveV2Pool(CURVE_CVXPRISMA_PRISMA_POOL);
    ICurveV2Pool mkUsdPrismaSwap = ICurveV2Pool(CURVE_PRISMA_MKUSD_POOL);

    /// @notice Swap native ETH <-> CVX on Curve
    /// @param amount - amount to swap
    /// @param minAmountOut - minimum expected amount of output tokens
    /// @param ethToCvx - whether to swap from eth to cvx or the inverse
    /// @return amount of CVX obtained after the swap
    function _swapEthCvx(
        uint256 amount,
        uint256 minAmountOut,
        bool ethToCvx
    ) internal returns (uint256) {
        return
            cvxEthSwap.exchange_underlying{value: ethToCvx ? amount : 0}(
                ethToCvx ? CVXETH_ETH_INDEX : CVXETH_CVX_INDEX,
                ethToCvx ? CVXETH_CVX_INDEX : CVXETH_ETH_INDEX,
                amount,
                minAmountOut
            );
    }

    /// @notice Swap ETH<->Prisma on Curve
    /// @param amount - amount to swap
    /// @param minAmountOut - minimum expected amount of output tokens
    /// @param ethToPrisma - whether to swap from eth to prisma or the inverse
    /// @return amount of token obtained after the swap
    function _swapEthPrisma(
        uint256 amount,
        uint256 minAmountOut,
        bool ethToPrisma
    ) internal returns (uint256) {
        return
            prismaEthSwap.exchange_underlying{value: ethToPrisma ? amount : 0}(
                ethToPrisma ? PRISMAETH_ETH_INDEX : PRISMAETH_PRISMA_INDEX,
                ethToPrisma ? PRISMAETH_PRISMA_INDEX : PRISMAETH_ETH_INDEX,
                amount,
                minAmountOut
            );
    }

    /// @notice Swap mkUSD<->Prisma on Curve
    /// @param amount - amount to swap
    /// @param minAmountOut - minimum expected amount of output tokens
    /// @param mkUsdToPrisma - whether to swap from mkUsd to prisma or the inverse
    /// @return amount of token obtained after the swap
    function _swapMkUsdPrisma(
        uint256 amount,
        uint256 minAmountOut,
        bool mkUsdToPrisma
    ) internal returns (uint256) {
        return
            mkUsdPrismaSwap.exchange_underlying(
                mkUsdToPrisma
                    ? PRISMAMKUSD_MKUSD_INDEX
                    : PRISMAMKUSD_PRISMA_INDEX,
                mkUsdToPrisma
                    ? PRISMAMKUSD_PRISMA_INDEX
                    : PRISMAMKUSD_MKUSD_INDEX,
                amount,
                minAmountOut
            );
    }

    /// @notice Swap cvxPrisma<->Prisma on Curve
    /// @param amount - amount to swap
    /// @param minAmountOut - minimum expected amount of output tokens
    /// @param cvxPrismaToPrisma - whether to swap from cvxPrisma to prisma or the inverse
    /// @return amount of token obtained after the swap
    function _swapCvxPrismaPrisma(
        uint256 amount,
        uint256 minAmountOut,
        bool cvxPrismaToPrisma
    ) internal returns (uint256) {
        return
            cvxPrismaPrismaSwap.exchange(
                cvxPrismaToPrisma
                    ? PRISMACVXPRISMA_CVXPRISMA_INDEX
                    : PRISMACVXPRISMA_PRISMA_INDEX,
                cvxPrismaToPrisma
                    ? PRISMACVXPRISMA_PRISMA_INDEX
                    : PRISMACVXPRISMA_CVXPRISMA_INDEX,
                amount,
                minAmountOut
            );
    }

    receive() external payable {}
}
