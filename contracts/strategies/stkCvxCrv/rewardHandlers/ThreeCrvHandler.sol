// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "./HandlerBase.sol";
import "../../../../interfaces/ICurvePool.sol";
import "../../../../interfaces/ICurveTriCrypto.sol";

contract ThreeCrvHandler is stkCvxCrvHandlerBase {
    using SafeERC20 for IERC20;

    address private constant TRIPOOL =
        0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7;
    address private constant THREECRV_TOKEN =
        0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490;
    address private constant USDT_TOKEN =
        0xdAC17F958D2ee523a2206206994597C13D831ec7;
    address private constant TRICRYPTO =
        0xD51a44d3FaE010294C616388b506AcdA1bfAAE46;

    bool public useOracle = true;

    ICurvePool private tripool = ICurvePool(TRIPOOL);
    ICurveTriCrypto private tricrypto = ICurveTriCrypto(TRICRYPTO);

    constructor(address _strategy) stkCvxCrvHandlerBase(_strategy) {}

    /// @notice Set approvals for the contracts used when swapping & staking
    function setApprovals() external {
        IERC20(USDT_TOKEN).safeApprove(TRICRYPTO, 0);
        IERC20(USDT_TOKEN).safeApprove(TRICRYPTO, type(uint256).max);

        IERC20(THREECRV_TOKEN).safeApprove(TRIPOOL, 0);
        IERC20(THREECRV_TOKEN).safeApprove(TRIPOOL, type(uint256).max);
    }

    /// @notice Compute a min amount out based on pool oracle and set slippage
    /// @param _amount - amount to swap
    /// @return min acceptable amount of ETH
    function _calcMinAmountOut(uint256 _amount) internal returns (uint256) {
        /// assume peg/balance for 3crv pricing in USDT
        uint256 _virtualPrice = tripool.get_virtual_price();
        uint256 _usdtAmount = (_amount * _virtualPrice) / 1e18;
        /// get ETH price in USDT from tricrypto
        uint256 _ethUsdPrice = tricrypto.price_oracle(1);
        uint256 _amountEth = (_usdtAmount * _ethUsdPrice) / 1e18;
        return ((_amountEth * allowedSlippage) / DECIMALS);
    }

    /// @notice Turns oracle on or off for swap
    function switchOracle() external onlyOwner {
        useOracle = !useOracle;
    }

    function _threeCrvToEth(uint256 _amount) internal {
        uint256 _minAmountOut = useOracle ? _calcMinAmountOut(_amount) : 0;
        tripool.remove_liquidity_one_coin(_amount, 2, 0);
        uint256 _usdtBalance = IERC20(USDT_TOKEN).balanceOf(address(this));
        if (_usdtBalance > 0) {
            tricrypto.exchange(0, 2, _usdtBalance, 0, true);
        }
    }

    /// @notice Swap 3CRV for ETH on Curve
    /// @param _amount - amount to swap
    function sell(uint256 _amount) external override onlyStrategy {
        IERC20(THREECRV_TOKEN).transferFrom(msg.sender, address(this), _amount);
        _threeCrvToEth(_amount);
        (bool success, ) = (msg.sender).call{value: address(this).balance}("");
        require(success, "ETH transfer failed");
    }
}
