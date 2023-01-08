// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "./HandlerBase.sol";
import "../../../../interfaces/ICurveV2Pool.sol";

contract CvxHandler is stkCvxCrvHandlerBase {
    using SafeERC20 for IERC20;
    address public constant CVX_TOKEN =
        0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B;
    address public constant CURVE_CVX_ETH_POOL =
        0xB576491F1E6e5E62f1d8F26062Ee822B40B0E0d4;
    bool public useOracle = true;

    ICurveV2Pool cvxEthSwap = ICurveV2Pool(CURVE_CVX_ETH_POOL);

    /// @notice Set approvals for the contracts used when swapping & staking
    function setApprovals() external {
        IERC20(CVX_TOKEN).safeApprove(CURVE_CVX_ETH_POOL, 0);
        IERC20(CVX_TOKEN).safeApprove(CURVE_CVX_ETH_POOL, type(uint256).max);
    }

    /// @notice Compute a min amount out based on pool oracle and set slippage
    /// @param _amount - amount to swap
    /// @return min acceptable amount of ETH
    function _calcMinAmountOut(uint256 _amount) internal returns (uint256) {
        uint256 _cvxEthPrice = cvxEthSwap.price_oracle();
        uint256 _amountEthPrice = (_amount * _cvxEthPrice) / 1e18;
        return ((_amountEthPrice * allowedSlippage) / DECIMALS);
    }

    /// @notice Turns oracle on or off for swap
    function switchOracle() external onlyOwner {
        useOracle = !useOracle;
    }

    function _cvxToEth(uint256 _amount) internal returns (uint256) {
        uint256 _minAmountOut = useOracle ? _calcMinAmountOut(_amount) : 0;
        return
            cvxEthSwap.exchange_underlying{value: 0}(
                1,
                0,
                _amount,
                _minAmountOut
            );
    }

    /// @notice Swap native CVX for ETH on Curve
    /// @param _amount - amount to swap
    /// @return amount of ETH obtained after the swap
    function sell(uint256 _amount) external override returns (uint256) {
        IERC20(CVX_TOKEN).transferFrom(msg.sender, address(this), _amount);
        uint256 _ethAmount = _cvxToEth(_amount);
        (bool success, ) = (msg.sender).call{value: _ethAmount}("");
        require(success, "ETH transfer failed");
        return _ethAmount;
    }
}
