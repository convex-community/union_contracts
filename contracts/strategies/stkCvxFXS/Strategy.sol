// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "../../../interfaces/IBooster.sol";
import "../../../interfaces/IStrategyOracle.sol";
import "../../../interfaces/IGenericVault.sol";
import "../../../interfaces/ICvxFxsStaking.sol";

contract stkCvxFxsStrategy is Ownable {
    using SafeERC20 for IERC20;
    address public constant CVXFXS_TOKEN =
        0xFEEf77d3f69374f66429C91d732A244f074bdf74;

    address public immutable vault;
    ICvxFxsStaking constant cvxFxsStaking =
        ICvxFxsStaking(0x49b4d1dF40442f0C31b1BbAEA3EDE7c38e37E31a);

    address public harvester;
    uint256 public constant FEE_DENOMINATOR = 10000;

    constructor(address _vault) {
        vault = _vault;
    }

    /// @notice Set approvals for the contracts used when swapping & staking
    function setApprovals() external {
        IERC20(CVXFXS_TOKEN).safeApprove(address(cvxFxsStaking), 0);
        IERC20(CVXFXS_TOKEN).safeApprove(
            address(cvxFxsStaking),
            type(uint256).max
        );
    }

    /// @notice Update the harvester contract
    /// @param _harvester address of the new contract
    function setHarvester(address _harvester) external onlyOwner {
        require(_harvester != address(0));
        harvester = _harvester;
        // ensures all rewards are redirected to harvester
        // if regular claim reward is triggered on staking contract
        cvxFxsStaking.setRewardRedirect(harvester);
    }

    /// @notice Query the amount currently staked
    /// @return total - the total amount of tokens staked
    function totalUnderlying() public view returns (uint256 total) {
        return cvxFxsStaking.balanceOf(address(this));
    }

    /// @notice Deposits all underlying tokens in the staking contract
    function stake(uint256 _amount) external onlyVault {
        cvxFxsStaking.stake(_amount);
    }

    /// @notice Withdraw a certain amount from the staking contract
    /// @param _amount - the amount to withdraw
    /// @dev Can only be called by the vault
    function withdraw(uint256 _amount) external onlyVault {
        cvxFxsStaking.withdraw(_amount);
        IERC20(CVXFXS_TOKEN).safeTransfer(vault, _amount);
    }

    /// @notice Claim rewards and swaps them to cvxFXS for restaking
    /// @dev Can be called by the vault only
    /// @param _caller - the address calling the harvest on the vault
    /// @param _minAmountOut - min amount of cvxFxs expected
    /// @return harvested - the amount harvested
    function harvest(address _caller, uint256 _minAmountOut)
        external
        onlyVault
        returns (uint256 harvested)
    {
        // claim rewards
        cvxFxsStaking.getReward(address(this), harvester);

        uint256 _cvxFxsBalance = IERC20(CVXFXS_TOKEN).balanceOf(address(this));
        require(_cvxFxsBalance >= _minAmountOut, "slippage");

        uint256 _stakingAmount = _cvxFxsBalance;

        if (_cvxFxsBalance > 0) {
            // if this is the last call, no fees
            if (IGenericVault(vault).totalSupply() != 0) {
                // Deduce and pay out incentive to caller (not needed for final exit)
                if (IGenericVault(vault).callIncentive() > 0) {
                    uint256 incentiveAmount = (_cvxFxsBalance *
                        IGenericVault(vault).callIncentive()) / FEE_DENOMINATOR;
                    IERC20(CVXFXS_TOKEN).safeTransfer(_caller, incentiveAmount);
                    _stakingAmount = _stakingAmount - incentiveAmount;
                }
                // Deduce and pay platform fee
                if (IGenericVault(vault).platformFee() > 0) {
                    uint256 feeAmount = (_cvxFxsBalance *
                        IGenericVault(vault).platformFee()) / FEE_DENOMINATOR;
                    IERC20(CVXFXS_TOKEN).safeTransfer(
                        IGenericVault(vault).platform(),
                        feeAmount
                    );
                    _stakingAmount = _stakingAmount - feeAmount;
                }
            }
            // Stake on Convex
            cvxFxsStaking.stakeAll();
        }

        return _stakingAmount;
    }

    /// @notice Transfers an ERC20 stuck in the contract to designated address
    /// @param _token - token address (can not be staking token)
    /// @param _to - address to send token to
    /// @param _amount - amount to transfer
    function rescueToken(
        address _token,
        address _to,
        uint256 _amount
    ) external onlyOwner {
        require(
            _token != address(cvxFxsStaking),
            "Cannot rescue staking token"
        );
        IERC20(_token).safeTransfer(_to, _amount);
    }

    modifier onlyVault() {
        require(vault == msg.sender, "Vault calls only");
        _;
    }
}
