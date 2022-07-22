// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "../../../interfaces/IStrategy.sol";

contract AuraBalStrategy is Ownable, IStrategy {
    using SafeERC20 for IERC20;

    address public immutable vault;

    uint256 public constant FEE_DENOMINATOR = 10000;

    address private constant AURABAL_PT_DEPOSIT =
    0xeAd792B55340Aa20181A80d6a16db6A0ECd1b827;
    address private constant AURABAL_STAKING =
    0x5e5ea2048475854a5702F5B8468A51Ba1296EFcC;
    address private constant AURABAL_TOKEN =
    0x616e8BfA43F920657B3497DBf40D6b1A02D4608d;
    address private constant AURA_TOKEN =
    0xC0c293ce456fF0ED870ADd98a0828Dd4d2903DBF;
    address private constant USBB_TOKEN =
    0x7B50775383d3D6f0215A8F290f2C9e2eEBBEceb2;
    IBasicRewards private auraBalStaking = IBasicRewards(AURABAL_STAKING);


    constructor(address _vault) {
        vault = _vault;
    }

    /// @notice Set approvals for the contracts used when swapping & staking
    function setApprovals() external {
        IERC20(AURABAL_TOKEN).safeApprove(AURABAL_STAKING, 0);
        IERC20(AURABAL_TOKEN).safeApprove(AURABAL_STAKING, type(uint256).max);
    }

    /// @notice Query the amount currently staked
    /// @return total - the total amount of tokens staked
    function totalUnderlying() public view returns (uint256 total) {
        return auraBalStaking.balanceOf(address(this));
    }

    /// @notice Deposits underlying tokens in the staking contract
    function stake(uint256 _amount) external onlyVault {
        auraBalStaking.stake(_amount);
    }

    /// @notice Withdraw a certain amount from the staking contract
    /// @param _amount - the amount to withdraw
    /// @dev Can only be called by the vault
    function withdraw(uint256 _amount) external onlyVault {
        auraBalStaking.withdraw(_amount, false);
        IERC20(AURABAL_TOKEN).safeTransfer(vault, _amount);
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
        auraBalStaking.getReward();

        // sell AURA rewards for ETH
        uint256 _auraBalance = IERC20(AURA_TOKEN).balanceOf(address(this));
        if (_auraBalance > 0) {
            _swapAuraToEth(_auraBalance);
        }

        // sell usd-BB rewards for ETH
        uint256 _usbbBalance = IERC20(USBB_TOKEN).balanceOf(address(this));
        if (_usbbBalance > 0) {
            _swapUsbbToEth(_usbbBalance);
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
            // check if there is a premium on cvxFXS
            if (cvxFxsFxsSwap.price_oracle() > 1 ether) {
                // lock and deposit as cvxFxs
                ICvxFxsDeposit(FXS_DEPOSIT).deposit(_stakingAmount, true);
                _staked = cvxFxsFxsSwap.add_liquidity([0, _stakingAmount], 0);
            }
            // If not add liquidity on Curve
            else {
                _staked = cvxFxsFxsSwap.add_liquidity([_stakingAmount, 0], 0);
            }
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
