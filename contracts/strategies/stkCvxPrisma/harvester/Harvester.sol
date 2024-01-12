// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "../../../../interfaces/IVaultRewardHandler.sol";
import "../../../../interfaces/ICurvePool.sol";
import "../../../../interfaces/ICurveTriCrypto.sol";
import "../../../../interfaces/ICurveV2Pool.sol";
import "../../../../interfaces/ICvxCrvDeposit.sol";
import "../../../../interfaces/ICurveFactoryPool.sol";
import "../StrategyBase.sol";

contract stkCvxPrismaHarvester is stkCvxPrismaStrategyBase {
    using SafeERC20 for IERC20;
    address public owner;
    address public immutable strategy;
    uint256 public allowedSlippage = 9700;
    uint256 public constant DECIMALS = 10000;
    address public pendingOwner;

    bool public useOracle = true;
    bool public forceLock;

    constructor(address _strategy) {
        strategy = _strategy;
        owner = msg.sender;
    }

    /// @notice Set approvals for the contracts used when swapping & staking
    function setApprovals() external {
        IERC20(CVX_TOKEN).safeApprove(CURVE_CVX_ETH_POOL, 0);
        IERC20(CVX_TOKEN).safeApprove(CURVE_CVX_ETH_POOL, type(uint256).max);

        IERC20(MKUSD_TOKEN).safeApprove(CURVE_PRISMA_MKUSD_POOL, 0);
        IERC20(MKUSD_TOKEN).safeApprove(
            CURVE_PRISMA_MKUSD_POOL,
            type(uint256).max
        );

        IERC20(PRISMA_TOKEN).safeApprove(PRISMA_DEPOSIT, 0);
        IERC20(PRISMA_TOKEN).safeApprove(PRISMA_DEPOSIT, type(uint256).max);

        IERC20(PRISMA_TOKEN).safeApprove(CURVE_CVXPRISMA_PRISMA_POOL, 0);
        IERC20(PRISMA_TOKEN).safeApprove(
            CURVE_CVXPRISMA_PRISMA_POOL,
            type(uint256).max
        );
    }

    /// @notice Turns oracle on or off for swap
    function switchOracle() external onlyOwner {
        useOracle = !useOracle;
    }

    /// @notice Sets the contract's future owner
    /// @param _po - pending owner's address
    function setPendingOwner(address _po) external onlyOwner {
        pendingOwner = _po;
    }

    /// @notice Allows a pending owner to accept ownership
    function acceptOwnership() external {
        require(pendingOwner == msg.sender, "only new owner");
        owner = pendingOwner;
        pendingOwner = address(0);
    }

    /// @notice switch the forceLock option to force harvester to lock
    /// @dev the harvester will lock even if there is a discount if forceLock is true
    function setForceLock() external onlyOwner {
        forceLock = !forceLock;
    }

    /// @notice Rescue tokens wrongly sent to the contracts or claimed extra
    /// rewards that the contract is not equipped to handle
    /// @dev Unhandled rewards can be redirected to new harvester contract
    function rescueToken(address _token, address _to) external onlyOwner {
        /// Only allow to rescue non-supported tokens
        require(
            _token != MKUSD_TOKEN &&
                _token != PRISMA_TOKEN &&
                _token != CVX_TOKEN,
            "not allowed"
        );
        IERC20 _t = IERC20(_token);
        uint256 _balance = _t.balanceOf(address(this));
        _t.safeTransfer(_to, _balance);
    }

    /// @notice Sets the range of acceptable slippage & price impact
    function setSlippage(uint256 _slippage) external onlyOwner {
        allowedSlippage = _slippage;
    }

    /// @notice Compute a min amount of Prisma bought for CVX sold based on pool oracle for cvx/eth & prisma/eth
    /// @param _amount - amount to swap
    /// @return min acceptable amount of Prisma
    function _calcMinAmountOutCvxPrisma(
        uint256 _amount
    ) internal returns (uint256) {
        uint256 _cvxEthPrice = cvxEthSwap.price_oracle();
        uint256 _ethPrismaPrice = prismaEthSwap.price_oracle();
        uint256 _amountEthPrice = (_amount * _cvxEthPrice) / 1e18;
        uint256 _amountPrismaPrice = (_amountEthPrice * 1e18) / _ethPrismaPrice;
        return ((_amountPrismaPrice * allowedSlippage) / DECIMALS);
    }

    /// @notice Compute a min amount of Prisma bought for mkUSD sold based on pool oracle for mkusd/Prisma
    /// @param _amount - amount to swap
    /// @return min acceptable amount of Prisma
    function _calcMinAmountOutMkUsdPrisma(
        uint256 _amount
    ) internal returns (uint256) {
        uint256 _prismaMkUsdPrice = mkUsdPrismaSwap.price_oracle();
        uint256 _amountPrismaPrice = (_amount * 1e18) / _prismaMkUsdPrice;
        return ((_amountPrismaPrice * allowedSlippage) / DECIMALS);
    }

    function processRewards()
        external
        onlyStrategy
        returns (uint256 _harvested)
    {
        // swap cvx to eth
        uint256 _cvxBalance = IERC20(CVX_TOKEN).balanceOf(address(this));
        if (_cvxBalance > 0) {
            _swapEthCvx(_cvxBalance, 0, false);
        }
        uint256 _ethBalance = address(this).balance;
        _harvested = 0;

        // swap eth to prisma
        if (_ethBalance > 0) {
            _swapEthPrisma(
                _ethBalance,
                useOracle ? _calcMinAmountOutCvxPrisma(_cvxBalance) : 0,
                true
            );
        }

        // handle mkusd rewards
        uint256 _mkUsdBalance = IERC20(MKUSD_TOKEN).balanceOf(address(this));
        // swap to prisma
        if (_mkUsdBalance > 0) {
            _swapMkUsdPrisma(
                _mkUsdBalance,
                useOracle ? _calcMinAmountOutMkUsdPrisma(_mkUsdBalance) : 0,
                true
            );
        }

        uint256 _prismaBalance = IERC20(PRISMA_TOKEN).balanceOf(address(this));
        if (_prismaBalance > 0) {
            uint256 _oraclePrice = cvxPrismaPrismaSwap.price_oracle();
            // check if there is a premium on cvxPrisma or if we want to lock
            if (_oraclePrice > 1 ether || forceLock) {
                // lock and deposit as cvxPrisma
                cvxPrismaDeposit.deposit(_prismaBalance, true);
                _harvested = _prismaBalance;
            }
            // If not swap on Curve
            else {
                uint256 _minCvxPrismaAmountOut = 0;
                if (useOracle) {
                    _minCvxPrismaAmountOut =
                        (_prismaBalance * _oraclePrice) /
                        1e18;
                    _minCvxPrismaAmountOut = ((_minCvxPrismaAmountOut *
                        allowedSlippage) / DECIMALS);
                }
                _harvested = cvxPrismaPrismaSwap.exchange_underlying(
                    0,
                    1,
                    _prismaBalance,
                    _minCvxPrismaAmountOut
                );
            }
            IERC20(CVXPRISMA_TOKEN).safeTransfer(msg.sender, _harvested);
        }
        return _harvested;
    }

    modifier onlyOwner() {
        require((msg.sender == owner), "owner only");
        _;
    }

    modifier onlyStrategy() {
        require((msg.sender == strategy), "strategy only");
        _;
    }
}
