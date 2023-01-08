// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "../../../interfaces/IGenericVault.sol";
import "../../../interfaces/IStrategy.sol";
import "../../../interfaces/IRewards.sol";
import "../../../interfaces/ICvxCrvStaking.sol";
import "../../../interfaces/IVaultRewardHandler.sol";
import "./StrategyBase.sol";

contract stkCvxCrvStrategy is Ownable, stkCvxCrvStrategyBase {
    using SafeERC20 for IERC20;

    address public immutable vault;
    ICvxCrvStaking public immutable cvxCrvStaking;
    address[] public rewardTokens;
    mapping(address => address) public rewardHandlers;

    uint256 public constant FEE_DENOMINATOR = 10000;

    constructor(address _vault, address _staking) {
        vault = _vault;
        cvxCrvStaking = ICvxCrvStaking(_staking);
    }

    /// @notice Set approvals for the contracts used when swapping & staking
    function setApprovals() external {
        address[] memory _rewardTokens = rewardTokens;
        for (uint256 i; i < _rewardTokens.length; ++i) {
            address _tokenHandler = rewardHandlers[_rewardTokens[i]];
            if (_tokenHandler == address(0)) {
                continue;
            }
            IERC20(_rewardTokens[i]).safeApprove(_tokenHandler, 0);
            IERC20(_rewardTokens[i]).safeApprove(
                _tokenHandler,
                type(uint256).max
            );
        }
    }

    /// @notice update the token to handler mapping
    function _updateRewardToken(
        address _token,
        address _handler,
        bool _approve
    ) internal {
        rewardHandlers[_token] = _handler;
        if (_approve) {
            IERC20(_token).safeApprove(_handler, 0);
            IERC20(_token).safeApprove(_handler, type(uint256).max);
        }
    }

    /// @notice Add a reward token and its handler
    /// @dev For tokens that should not be swapped (i.e. BAL rewards)
    ///      use address as zero handler
    /// @param _token the reward token to add
    /// @param _handler address of the contract that will sell for BAL or ETH
    /// @param _approve whether to approve token spending for handler contract
    function addRewardToken(
        address _token,
        address _handler,
        bool _approve
    ) external onlyOwner {
        // avoid adding the same token twice
        require(rewardHandlers[_token] != address(0), "already exists");
        rewardTokens.push(_token);
        _updateRewardToken(_token, _handler, _approve);
    }

    /// @notice Update the handler of a reward token
    /// @dev Used to update a handler or retire a token (set handler to address 0)
    /// @dev Handler contracts sell for ETH or the token
    /// @param _token the reward token to add
    /// @param _handler address of the contract that will sell the token or ETH (or vice versa)
    /// @param _approve whether to approve token spending for handler contract
    function updateRewardToken(
        address _token,
        address _handler,
        bool _approve
    ) external onlyOwner {
        _updateRewardToken(_token, _handler, _approve);
    }

    /// @notice Reset all registered reward tokens
    function clearRewardTokens() external onlyOwner {
        address[] memory _rewardTokens = rewardTokens;
        for (uint256 i; i < _rewardTokens.length; i++) {
            rewardHandlers[_rewardTokens[i]] = address(0);
        }
        delete (rewardTokens);
    }

    /// @notice returns the number of reward tokens
    /// @return the number of reward tokens
    function totalRewardTokens() external view returns (uint256) {
        return rewardTokens.length;
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
        // claim rewards
        cvxCrvStaking.getReward(address(this));

        // process rewards
        address[] memory _rewardTokens = rewardTokens;
        // swap all reward tokens for ETH through their respective handlers
        for (uint256 i; i < _rewardTokens.length; ++i) {
            address _tokenHandler = rewardHandlers[_rewardTokens[i]];
            if (_tokenHandler == address(0)) {
                continue;
            }
            uint256 _tokenBalance = IERC20(_rewardTokens[i]).balanceOf(
                address(this)
            );
            if (_tokenBalance > 0) {
                IVaultRewardHandler(_tokenHandler).sell(_tokenBalance);
            }
        }

        return 0;
    }

    modifier onlyVault() {
        require(vault == msg.sender, "Vault calls only");
        _;
    }
}
