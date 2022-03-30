// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "../../../interfaces/IStrategy.sol";
import "../../../interfaces/IGenericVault.sol";
import "../../../interfaces/IBasicRewards.sol";

contract PCvxStrategy is Ownable, IStrategy {
    using SafeERC20 for IERC20;

    address public immutable vault;
    address public stakingRewards;
    address public immutable pCVX;

    uint256 public constant FEE_DENOMINATOR = 10000;

    constructor(
        address _vault,
        address _rewards,
        address _pcvx
    ) {
        vault = _vault;
        stakingRewards = _rewards;
        pCVX = _pcvx;
    }

    /// @notice Set approvals for the contracts used when swapping & staking
    function setApprovals() external {
        IERC20(pCVX).safeApprove(stakingRewards, 0);
        IERC20(pCVX).safeApprove(stakingRewards, type(uint256).max);
    }

    /// @notice Query the amount currently staked
    /// @return total - the total amount of tokens staked
    function totalUnderlying() public view returns (uint256 total) {
        return IBasicRewards(stakingRewards).balanceOf(address(this));
    }

    /// @notice Deposits all underlying tokens in the staking contract
    function stake(uint256 _amount) external onlyVault {
        IBasicRewards(stakingRewards).stake(_amount);
    }

    /// @notice Withdraw a certain amount from the staking contract
    /// @param _amount - the amount to withdraw
    /// @dev Can only be called by the vault
    function withdraw(uint256 _amount) external onlyVault {
        IBasicRewards(stakingRewards).withdraw(_amount, false);
        IERC20(pCVX).safeTransfer(vault, _amount);
    }

    /// @notice Claim rewards and restakes them
    /// @dev Can be called by the vault only
    /// @param _caller - the address calling the harvest on the vault
    /// @return harvested - the amount harvested
    function harvest(address _caller)
        external
        onlyVault
        returns (uint256 harvested)
    {
        // claim rewards
        IBasicRewards(stakingRewards).getReward();

        uint256 _pCvxBalance = IERC20(pCVX).balanceOf(address(this));

        uint256 _stakingAmount = _pCvxBalance;

        if (_pCvxBalance > 0) {
            // if this is the last call, no fees
            if (IGenericVault(vault).totalSupply() != 0) {
                // Deduce and pay out incentive to caller (not needed for final exit)
                if (IGenericVault(vault).callIncentive() > 0) {
                    uint256 incentiveAmount = (_pCvxBalance *
                        IGenericVault(vault).callIncentive()) / FEE_DENOMINATOR;
                    IERC20(pCVX).safeTransfer(_caller, incentiveAmount);
                    _stakingAmount -= incentiveAmount;
                }
                // Deduce and pay platform fee
                if (IGenericVault(vault).platformFee() > 0) {
                    uint256 feeAmount = (_pCvxBalance *
                        IGenericVault(vault).platformFee()) / FEE_DENOMINATOR;
                    IERC20(pCVX).safeTransfer(
                        IGenericVault(vault).platform(),
                        feeAmount
                    );
                    _stakingAmount -= feeAmount;
                }
            }
            // Restake
            IBasicRewards(stakingRewards).stake(_stakingAmount);
        }
        return _stakingAmount;
    }

    modifier onlyVault() {
        require(vault == msg.sender, "Vault calls only");
        _;
    }
}
