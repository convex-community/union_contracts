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

    address private constant TRIPOOL =
    0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7;
    address private constant THREECRV_TOKEN =
    0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490;
    address private constant USDT_TOKEN =
    0xdAC17F958D2ee523a2206206994597C13D831ec7;
    address private constant TRICRYPTO =
    0xD51a44d3FaE010294C616388b506AcdA1bfAAE46;
    address private constant CVX_MINING_LIB =
    0x3c75BFe6FbfDa3A94E7E7E8c2216AFc684dE5343;
    address private constant THREE_CRV_REWARDS =
    0x7091dbb7fcbA54569eF1387Ac89Eb2a5C9F6d2EA;
    address private constant CVXCRV_DEPOSIT =
    0x8014595F2AB54cD7c604B00E9fb932176fDc86Ae;
    uint256 public constant FEE_DENOMINATOR = 10000;

    uint256 private constant PID = 72;

    constructor(address _vault)  {
        vault = _vault;
    }

    /// @notice Set approvals for the contracts used when swapping & staking
    function setApprovals() override external {

        IERC20(CVX_TOKEN).safeApprove(CURVE_CVX_ETH_POOL, 0);
        IERC20(CVX_TOKEN).safeApprove(CURVE_CVX_ETH_POOL, type(uint256).max);

        IERC20(CRV_TOKEN).safeApprove(CVXCRV_DEPOSIT, 0);
        IERC20(CRV_TOKEN).safeApprove(CVXCRV_DEPOSIT, type(uint256).max);

        IERC20(FXS_TOKEN).safeApprove(CURVE_CVXFXS_FXS_POOL, 0);
        IERC20(FXS_TOKEN).safeApprove(CURVE_CVXFXS_FXS_POOL, type(uint256).max);

        IERC20(CURVE_CVXFXS_FXS_LP_TOKEN).safeApprove(BOOSTER, 0);
        IERC20(CURVE_CVXFXS_FXS_LP_TOKEN).safeApprove(BOOSTER, type(uint256).max);

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
    function withdraw(uint256 _amount) external onlyVault() {
        booster.withdraw(PID, _amount);
        IERC20(CURVE_CVXFXS_FXS_LP_TOKEN).safeTransfer(vault, _amount);
    }

    /// @notice Claim rewards and swaps them to FXS for restaking
    /// @dev Can be called by the vault only
    /// @param _platformFee - the platform fee
    /// @param _callIncentive - the caller fee
    /// @param _caller - the address calling the harvest on the vault
    /// @param _platform - the address receiving the platform fees
    /// @return harvested - the amount harvested
    function harvest(uint256 _platformFee,
        uint256 _callIncentive,
        address _caller,
        address _platform) external onlyVault() returns (uint256 harvested) {
        // claim rewards
        cvxFxsStaking.getReward();

        // sell CVX rewards for ETH
        uint256 _cvxBalance = IERC20(CVX_TOKEN).balanceOf(address(this));
        if (_cvxBalance > 0) {
            cvxEthSwap.exchange_underlying{value: 0}(
                1,
                0,
                _cvxBalance,
                0
            );
        }

        // sell CRV rewards for ETH
        uint256 _crvBalance = IERC20(CRV_TOKEN).balanceOf(address(this));
        if (_crvBalance > 0) {
            _swapCrvToEth(_crvBalance);
        }
        uint256 _ethBalance = address(this).balance;

        _swapEthForFxs(_ethBalance, swapOption);

        uint256 _fxsBalance = IERC20(FXS_TOKEN).balanceOf(address(this));

        // if this is the last call, no restake & no fees
        if (IGenericVault(vault).totalSupply() != 0) {

            if (_fxsBalance > 0) {
                uint256 _stakingAmount = _fxsBalance;
                // Deduce and pay out incentive to caller (not needed for final exit)
                if (_callIncentive > 0) {
                    uint256 incentiveAmount = (_fxsBalance * _callIncentive) /
                    FEE_DENOMINATOR;
                    IERC20(FXS_TOKEN).safeTransfer(_caller, incentiveAmount);
                    _stakingAmount = _stakingAmount - incentiveAmount;
                }
                // Deduce and pay platform fee
                if (_platformFee > 0) {
                    uint256 feeAmount = (_fxsBalance * _platformFee) /
                    FEE_DENOMINATOR;
                    IERC20(FXS_TOKEN).safeTransfer(_platform, feeAmount);
                    _stakingAmount = _stakingAmount - feeAmount;
                }

                // Add liquidity on Curve
                cvxFxsFxsSwap.add_liquidity([_stakingAmount, 0], 0);
                // Stake on Convex
                require(booster.depositAll(PID, true));
            }
        }
        return _fxsBalance;
    }


    modifier onlyVault() {
        require(vault == msg.sender, "Vault calls only");
        _;
    }
}