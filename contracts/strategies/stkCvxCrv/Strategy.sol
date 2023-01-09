// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "../../../interfaces/IGenericVault.sol";
import "../../../interfaces/IStrategy.sol";
import "../../../interfaces/IRewards.sol";
import "../../../interfaces/ICvxCrvStaking.sol";
import "../../../interfaces/IHarvester.sol";
import "./StrategyBase.sol";

contract stkCvxCrvStrategy is Ownable, stkCvxCrvStrategyBase {
    using SafeERC20 for IERC20;

    address public immutable vault;
    address public harvester;
    ICvxCrvStaking public immutable cvxCrvStaking;

    uint256 public constant FEE_DENOMINATOR = 10000;

    constructor(address _vault, address _staking) {
        vault = _vault;
        cvxCrvStaking = ICvxCrvStaking(_staking);
    }

    /// @notice Set approvals for the contracts used when swapping & staking
    function setApprovals() external {

    }

    /// @notice Update the harvester contract
    /// @param _harvester address of the new contract
    function updateHarvester(address _harvester) external onlyOwner {
        require(_harvester != address(0));
    }

    /// @notice Query the amount currently staked
    /// @return total - the total amount of tokens staked
    function totalUnderlying() public view returns (uint256 total) {
        return cvxCrvStaking.balanceOf(address(this));
    }

    /// @notice Deposits underlying tokens in the staking contract
    function stake(uint256 _amount) public onlyVault {
        cvxCrvStaking.stake(_amount, address(this));
    }

    /// @notice Withdraw a certain amount from the staking contract
    /// @param _amount - the amount to withdraw
    /// @dev Can only be called by the vault
    function withdraw(uint256 _amount) external onlyVault {
        cvxCrvStaking.withdraw(_amount);
        IERC20(CVXCRV_TOKEN).safeTransfer(vault, _amount);
    }

    /// @notice Claim rewards and swaps them to ETH then cvxCRV for restaking
    /// @dev Can be called by the vault only
    /// @param _caller - the address calling the harvest on the vault
    /// @param _minAmountOut -  min amount of LP tokens to receive w/o revert
    /// @param _lock - whether to lock or swap
    /// @return harvested - the amount harvested
    function harvest(
        address _caller,
        uint256 _minAmountOut,
        bool _lock
    ) public onlyVault returns (uint256 harvested) {
        // claim rewards to harvester
        cvxCrvStaking.getReward(address(this), harvester);

        // process rewards via harvester
        IHarvester(harvester).processRewards(_minAmountOut, _lock);

        return 0;
    }

    modifier onlyVault() {
        require(vault == msg.sender, "Vault calls only");
        _;
    }
}
