// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "./StrategyBase.sol";
import "../../../interfaces/IStrategy.sol";
import "../../../interfaces/IGenericVault.sol";

contract CvxFxsStrategy is Ownable, CvxFxsStrategyBase, IStrategy {
    using SafeERC20 for IERC20;

    address public immutable vault;

    uint256 public constant FEE_DENOMINATOR = 10000;

    uint256 private constant PID = 72;

    constructor(address _vault) {
        vault = _vault;
    }

    /// @notice Set approvals for the contracts used when swapping & staking
    function setApprovals() external {
        IERC20(CVX_TOKEN).safeApprove(CURVE_CVX_ETH_POOL, 0);
        IERC20(CVX_TOKEN).safeApprove(CURVE_CVX_ETH_POOL, type(uint256).max);

        IERC20(FXS_TOKEN).safeApprove(CURVE_CVXFXS_FXS_POOL, 0);
        IERC20(FXS_TOKEN).safeApprove(CURVE_CVXFXS_FXS_POOL, type(uint256).max);

        IERC20(CURVE_CVXFXS_FXS_LP_TOKEN).safeApprove(BOOSTER, 0);
        IERC20(CURVE_CVXFXS_FXS_LP_TOKEN).safeApprove(
            BOOSTER,
            type(uint256).max
        );

        IERC20(CRV_TOKEN).safeApprove(CURVE_CRV_ETH_POOL, 0);
        IERC20(CRV_TOKEN).safeApprove(CURVE_CRV_ETH_POOL, type(uint256).max);

        IERC20(CURVE_CVXFXS_FXS_LP_TOKEN).safeApprove(CURVE_CVXFXS_FXS_POOL, 0);
        IERC20(CURVE_CVXFXS_FXS_LP_TOKEN).safeApprove(
            CURVE_CVXFXS_FXS_POOL,
            type(uint256).max
        );

        IERC20(FRAX_TOKEN).safeApprove(UNISWAP_ROUTER, 0);
        IERC20(FRAX_TOKEN).safeApprove(UNISWAP_ROUTER, type(uint256).max);
    }

    /// @notice Query the amount currently staked
    /// @return total - the total amount of tokens staked
    function totalUnderlying() public view returns (uint256 total) {
        return cvxFxsStaking.balanceOf(address(this));
    }

    /// @notice Deposits all underlying tokens in the staking contract
    function stake(uint256 _amount) external {
        require(booster.deposit(PID, _amount, true));
    }

    /// @notice Change the default swap option for eth -> fxs
    /// @param _newOption - the new option to use
    function setSwapOption(SwapOption _newOption) external onlyOwner {
        SwapOption _oldOption = swapOption;
        swapOption = _newOption;
        emit OptionChanged(_oldOption, swapOption);
    }

    /// @notice Withdraw a certain amount from the staking contract
    /// @param _amount - the amount to withdraw
    /// @dev Can only be called by the vault
    function withdraw(uint256 _amount) external onlyVault {
        cvxFxsStaking.withdrawAndUnwrap(_amount, false);
        IERC20(CURVE_CVXFXS_FXS_LP_TOKEN).safeTransfer(vault, _amount);
    }

    /// @notice Claim rewards and swaps them to FXS for restaking
    /// @dev Can be called by the vault only
    /// @param _caller - the address calling the harvest on the vault
    /// @return harvested - the amount harvested
    function harvest(address _caller)
        external
        onlyVault
        returns (uint256 harvested)
    {
        // claim rewards
        cvxFxsStaking.getReward();

        // sell CVX rewards for ETH
        uint256 _cvxBalance = IERC20(CVX_TOKEN).balanceOf(address(this));
        if (_cvxBalance > 0) {
            _swapCvxToEth(_cvxBalance);
        }

        // sell CRV rewards for ETH
        uint256 _crvBalance = IERC20(CRV_TOKEN).balanceOf(address(this));
        if (_crvBalance > 0) {
            _swapCrvToEth(_crvBalance);
        }
        uint256 _ethBalance = address(this).balance;

        if (_ethBalance > 0) {
            _swapEthForFxs(_ethBalance, swapOption);
        }
        uint256 _fxsBalance = IERC20(FXS_TOKEN).balanceOf(address(this));

        uint256 _stakingAmount = _fxsBalance;
        uint256 _staked;

        if (_fxsBalance > 0) {
            // if this is the last call, no fees
            if (IGenericVault(vault).totalSupply() != 0) {
                // Deduce and pay out incentive to caller (not needed for final exit)
                if (IGenericVault(vault).callIncentive() > 0) {
                    uint256 incentiveAmount = (_fxsBalance *
                        IGenericVault(vault).callIncentive()) / FEE_DENOMINATOR;
                    IERC20(FXS_TOKEN).safeTransfer(_caller, incentiveAmount);
                    _stakingAmount = _stakingAmount - incentiveAmount;
                }
                // Deduce and pay platform fee
                if (IGenericVault(vault).platformFee() > 0) {
                    uint256 feeAmount = (_fxsBalance *
                        IGenericVault(vault).platformFee()) / FEE_DENOMINATOR;
                    IERC20(FXS_TOKEN).safeTransfer(
                        IGenericVault(vault).platform(),
                        feeAmount
                    );
                    _stakingAmount = _stakingAmount - feeAmount;
                }
            }

            // Add liquidity on Curve
            _staked = cvxFxsFxsSwap.add_liquidity([_stakingAmount, 0], 0);
            // Stake on Convex
            require(booster.depositAll(PID, true));
        }

        return _staked;
    }

    modifier onlyVault() {
        require(vault == msg.sender, "Vault calls only");
        _;
    }
}
