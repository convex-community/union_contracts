// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "./GenericDistributor.sol";
import "../../interfaces/IPirexCVX.sol";
import "../../interfaces/ILpxCvx.sol";
import "../../interfaces/ICurveV2Pool.sol";

contract CVXMerkleDistributor is GenericDistributor {
    using SafeERC20 for IERC20;

    address private constant PIREX_CVX =
        0x35A398425d9f1029021A92bc3d2557D42C8588D7;

    address private constant LPX_CVX =
        0x389fB29230D02e67eB963C1F5A00f2b16f95BEb7;

    ICurveV2Pool private constant LPXCVX_CVX_POOL =
        ICurveV2Pool(0x72725C0C879489986D213A9A6D2116dE45624c1c);

    // 2.5% slippage tolerance by default
    uint256 public slippage = 9750;
    uint256 private constant DECIMALS = 10000;

    constructor(
        address _vault,
        address _depositor,
        address _token
    ) GenericDistributor(_vault, _depositor, _token) {}

    /// @notice Set approvals for the tokens used when swapping
    function setApprovals() external override onlyAdmin {
        IERC20(token).safeApprove(vault, 0);
        IERC20(token).safeApprove(vault, type(uint256).max);
        IERC20(token).safeApprove(LPX_CVX, 0);
        IERC20(token).safeApprove(LPX_CVX, type(uint256).max);
    }

    /// @notice Set the acceptable level of slippage for LP deposits
    /// @dev As percentage of the ETH value of original amount in BIPS
    /// @param _slippage - the acceptable slippage threshold
    function setSlippage(uint256 _slippage) external onlyAdmin {
        slippage = _slippage;
    }

    /// @notice Stakes the contract's entire CVX balance in the Vault
    function stake() external override onlyAdminOrDistributor {
        uint256 _price = LPXCVX_CVX_POOL.price_oracle();
        uint256 _cvxBalance = IERC20(token).balanceOf(address(this));
        if (_price > 1) {
            IPirexCVX(PIREX_CVX).deposit(
                _cvxBalance,
                address(this),
                true,
                address(0)
            );
        } else {
            uint256 _minAmountOut = (_cvxBalance * _price) / 1e18;
            _minAmountOut = ((_minAmountOut * slippage) / DECIMALS);
            ILpxCvx(LPX_CVX).swap(
                ILpxCvx.Token.CVX,
                _cvxBalance,
                _minAmountOut,
                0,
                1
            );
        }
    }
}
