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

contract stkCvxFxsHarvester is stkCvxFxsStrategyBase {
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

        IERC20(FXS_TOKEN).safeApprove(CURVE_CVXFXS_FXS_POOL, 0);
        IERC20(FXS_TOKEN).safeApprove(CURVE_CVXFXS_FXS_POOL, type(uint256).max);

        IERC20(FXS_TOKEN).safeApprove(FXS_DEPOSIT, 0);
        IERC20(FXS_TOKEN).safeApprove(FXS_DEPOSIT, type(uint256).max);

        IERC20(FRAX_TOKEN).safeApprove(CURVE_FRAX_USDC_POOL, 0);
        IERC20(FRAX_TOKEN).safeApprove(CURVE_FRAX_USDC_POOL, type(uint256).max);

        IERC20(USDC_TOKEN).safeApprove(CURVE_FRAX_USDC_POOL, 0);
        IERC20(USDC_TOKEN).safeApprove(CURVE_FRAX_USDC_POOL, type(uint256).max);

        IERC20(USDC_TOKEN).safeApprove(UNIV3_ROUTER, 0);
        IERC20(USDC_TOKEN).safeApprove(UNIV3_ROUTER, type(uint256).max);

        IERC20(FRAX_TOKEN).safeApprove(UNIV3_ROUTER, 0);
        IERC20(FRAX_TOKEN).safeApprove(UNIV3_ROUTER, type(uint256).max);

        IERC20(FRAX_TOKEN).safeApprove(UNISWAP_ROUTER, 0);
        IERC20(FRAX_TOKEN).safeApprove(UNISWAP_ROUTER, type(uint256).max);
    }

    /// @notice Change the default swap option for eth -> fxs
    /// @param _newOption - the new option to use
    function setSwapOption(SwapOption _newOption) external onlyOwner {
        SwapOption _oldOption = swapOption;
        swapOption = _newOption;
        emit OptionChanged(_oldOption, swapOption);
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
        require(_token != FXS_TOKEN && _token != CVX_TOKEN, "not allowed");
        uint256 _balance = IERC20(_token).balanceOf(address(this));
        IERC20(_token).safeTransfer(_to, _balance);
    }

    /// @notice Sets the range of acceptable slippage & price impact
    function setSlippage(uint256 _slippage) external onlyOwner {
        allowedSlippage = _slippage;
    }

    /// @notice Compute a min amount of ETH based on pool oracle for cvx
    /// @param _amount - amount to swap
    /// @return min acceptable amount of ETH
    function _calcMinAmountOutCvxEth(uint256 _amount)
        internal
        returns (uint256)
    {
        uint256 _cvxEthPrice = cvxEthSwap.price_oracle();
        uint256 _amountEthPrice = (_amount * _cvxEthPrice) / 1e18;
        return ((_amountEthPrice * allowedSlippage) / DECIMALS);
    }

    function processRewards() external onlyStrategy returns (uint256) {
        uint256 _cvxBalance = IERC20(CVX_TOKEN).balanceOf(address(this));
        if (_cvxBalance > 0) {
            uint256 _minAmountOut = useOracle
                ? _calcMinAmountOutCvxEth(_cvxBalance)
                : 0;
            _cvxToEth(_cvxBalance, _minAmountOut);
        }
        uint256 _ethBalance = address(this).balance;
        uint256 _harvested = 0;

        if (_ethBalance > 0) {
            _swapEthForFxs(_ethBalance, swapOption);
        }

        uint256 _fxsBalance = IERC20(FXS_TOKEN).balanceOf(address(this));
        if (_fxsBalance > 0) {
            uint256 _oraclePrice = cvxFxsFxsSwap.price_oracle();
            // check if there is a premium on cvxFXS or if we want to lock
            if (_oraclePrice > 1 ether || forceLock) {
                // lock and deposit as cvxFxs
                cvxFxsDeposit.deposit(_fxsBalance, true);
                _harvested = _fxsBalance;
            }
            // If not swap on Curve
            else {
                uint256 _minCvxFxsAmountOut = 0;
                if (useOracle) {
                    uint256 _cvxEthPrice = cvxEthSwap.price_oracle();
                    _minCvxFxsAmountOut = (_fxsBalance * _oraclePrice) / 1e18;
                    _minCvxFxsAmountOut = ((_minCvxFxsAmountOut *
                        allowedSlippage) / DECIMALS);
                }
                _harvested = cvxFxsFxsSwap.exchange_underlying(
                    0,
                    1,
                    _fxsBalance,
                    _minCvxFxsAmountOut
                );
            }
            IERC20(CVXFXS_TOKEN).safeTransfer(msg.sender, _harvested);
            return _harvested;
        }
        return 0;
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
