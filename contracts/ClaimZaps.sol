// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "./UnionBase.sol";

contract ClaimZaps is ReentrancyGuard, UnionBase {
    using SafeERC20 for IERC20;

    // Possible options when claiming
    enum Option {
        Claim,
        ClaimAsETH,
        ClaimAsCRV,
        ClaimAsCVX,
        ClaimAndStake
    }

    /// @notice Set approvals for the tokens used when swapping
    function _setApprovals() internal {
        IERC20(CRV_TOKEN).safeApprove(CURVE_CRV_ETH_POOL, 0);
        IERC20(CRV_TOKEN).safeApprove(CURVE_CRV_ETH_POOL, type(uint256).max);

        IERC20(CVXCRV_TOKEN).safeApprove(CVXCRV_STAKING_CONTRACT, 0);
        IERC20(CVXCRV_TOKEN).safeApprove(
            CVXCRV_STAKING_CONTRACT,
            type(uint256).max
        );

        IERC20(CVXCRV_TOKEN).safeApprove(CURVE_CVXCRV_CRV_POOL, 0);
        IERC20(CVXCRV_TOKEN).safeApprove(
            CURVE_CVXCRV_CRV_POOL,
            type(uint256).max
        );
    }

    function _claimAs(
        address account,
        uint256 amount,
        Option option
    ) internal {
        _claim(account, amount, option, 0);
    }

    function _claimAs(
        address account,
        uint256 amount,
        Option option,
        uint256 minAmountOut
    ) internal {
        _claim(account, amount, option, minAmountOut);
    }

    /// @notice Zap function to claim token balance as another token
    /// @param account - recipient of the swapped token
    /// @param amount - amount to swap
    /// @param option - what to swap to
    /// @param minAmountOut - minimum desired amount of output token
    function _claim(
        address account,
        uint256 amount,
        Option option,
        uint256 minAmountOut
    ) internal nonReentrant {
        if (option == Option.ClaimAsCRV) {
            _swapCvxCrvToCrv(amount, account, minAmountOut);
        } else if (option == Option.ClaimAsETH) {
            uint256 _crvBalance = _swapCvxCrvToCrv(amount, address(this));
            uint256 _ethAmount = _swapCrvToEth(_crvBalance, minAmountOut);
            (bool success, ) = account.call{value: _ethAmount}("");
            require(success, "ETH transfer failed");
        } else if (option == Option.ClaimAsCVX) {
            uint256 _crvBalance = _swapCvxCrvToCrv(amount, address(this));
            uint256 _ethAmount = _swapCrvToEth(_crvBalance);
            uint256 _cvxAmount = _swapEthToCvx(_ethAmount, minAmountOut);
            IERC20(CVX_TOKEN).safeTransfer(account, _cvxAmount);
        } else if (option == Option.ClaimAndStake) {
            require(cvxCrvStaking.stakeFor(account, amount), "Staking failed");
        } else {
            IERC20(CVXCRV_TOKEN).safeTransfer(account, amount);
        }
    }
}
