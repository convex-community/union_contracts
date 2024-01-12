// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "../../../interfaces/IBooster.sol";
import "../../../interfaces/IStrategyOracle.sol";
import "../../../interfaces/IGenericVault.sol";
import "../../../interfaces/ICvxPrismaStaking.sol.sol";
import "../../../interfaces/IHarvester.sol";

error ZeroAddress();

contract stkCvxPrismaStrategy is Ownable {
    using SafeERC20 for IERC20;
    IERC20 private constant CVXPRISMA_TOKEN =
        IERC20(0x34635280737b5BFe6c7DC2FC3065D60d66e78185);

    address public immutable vault;
    ICvxPrismaStaking.sol private constant cvxPrismaStaking =
        ICvxPrismaStaking(0x0c73f1cFd5C9dFc150C8707Aa47Acbd14F0BE108);

    address public harvester;
    uint256 public constant FEE_DENOMINATOR = 10000;

    constructor(address _vault) {
        vault = _vault;
    }

    /// @notice Set approvals for the contracts used when swapping & staking
    function setApprovals() external {
        IERC20 _cvxPrisma = CVXPRISMA_TOKEN;
        _cvxPrisma.safeApprove(address(cvxPrismaStaking), 0);
        _cvxPrisma.safeApprove(address(cvxPrismaStaking), type(uint256).max);
    }

    /// @notice Update the harvester contract
    /// @param _harvester address of the new contract
    function setHarvester(address _harvester) external onlyOwner {
        if (_harvester == address(0)) revert ZeroAddress();
        harvester = _harvester;
        // ensures all rewards are redirected to harvester
        // if regular claim reward is triggered on staking contract
        cvxPrismaStaking.setRewardRedirect(_harvester);
    }

    /// @notice Query the amount currently staked
    /// @return total - the total amount of tokens staked
    function totalUnderlying() external view returns (uint256 total) {
        return cvxPrismaStaking.balanceOf(address(this));
    }

    /// @notice Deposits all underlying tokens in the staking contract
    function stake(uint256 _amount) external onlyVault {
        cvxPrismaStaking.stake(_amount);
    }

    /// @notice Withdraw a certain amount from the staking contract
    /// @param _amount - the amount to withdraw
    /// @dev Can only be called by the vault
    function withdraw(uint256 _amount) external onlyVault {
        cvxPrismaStaking.withdraw(_amount);
        CVXPRISMA_TOKEN.safeTransfer(vault, _amount);
    }

    /// @notice Claim rewards and swaps them to cvxPRISMA for restaking
    /// @dev Can be called by the vault only
    /// @param _caller - the address calling the harvest on the vault
    /// @param _minAmountOut - min amount of cvxPrisma expected
    /// @return harvested - the amount harvested
    function harvest(
        address _caller,
        uint256 _minAmountOut
    ) external onlyVault returns (uint256 harvested) {
        // claim rewards
        cvxPrismaStaking.getReward(address(this), harvester);

        uint256 _cvxPrismaBalance = IHarvester(harvester).processRewards();
        require(_cvxPrismaBalance >= _minAmountOut, "slippage");

        uint256 _stakingAmount = _cvxPrismaBalance;

        if (_cvxPrismaBalance > 0) {
            IERC20 _cvxPrisma = CVXPRISMA_TOKEN;
            IGenericVault _vault = IGenericVault(vault);
            // if this is the last call, no fees
            if (_vault.totalSupply() != 0) {
                // Deduce and pay out incentive to caller (not needed for final exit)
                if (_vault.callIncentive() > 0) {
                    uint256 incentiveAmount = (_cvxPrismaBalance *
                        _vault.callIncentive()) / FEE_DENOMINATOR;
                    _cvxPrisma.safeTransfer(_caller, incentiveAmount);
                    _stakingAmount = _stakingAmount - incentiveAmount;
                }
                // Deduce and pay platform fee
                if (_vault.platformFee() > 0) {
                    uint256 feeAmount = (_cvxPrismaBalance *
                        _vault.platformFee()) / FEE_DENOMINATOR;
                    _cvxPrisma.safeTransfer(_vault.platform(), feeAmount);
                    _stakingAmount = _stakingAmount - feeAmount;
                }
            }
            // Stake on Convex
            cvxPrismaStaking.stakeAll();
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
            _token != address(cvxPrismaStaking),
            "Cannot rescue staking token"
        );
        IERC20(_token).safeTransfer(_to, _amount);
    }

    modifier onlyVault() {
        require(vault == msg.sender, "Vault calls only");
        _;
    }
}
