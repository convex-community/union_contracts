// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "../../../interfaces/IGenericVault.sol";
import "../../../interfaces/IStrategy.sol";
import "../../../interfaces/IRewards.sol";
import "../../../interfaces/balancer/IRewardHandler.sol";
import "./StrategyBase.sol";

contract AuraBalStrategy is Ownable, AuraBalStrategyBase {
    using SafeERC20 for IERC20;

    address public immutable vault;
    address[] public rewardTokens;
    mapping(address => address) public rewardHandlers;

    uint256 public constant FEE_DENOMINATOR = 10000;

    constructor(address _vault) {
        vault = _vault;
    }

    /// @notice Set approvals for the contracts used when swapping & staking
    function setApprovals() external {
        IERC20(AURABAL_TOKEN).safeApprove(AURABAL_STAKING, 0);
        IERC20(AURABAL_TOKEN).safeApprove(AURABAL_STAKING, type(uint256).max);
        IERC20(BAL_TOKEN).safeApprove(BAL_VAULT, 0);
        IERC20(BAL_TOKEN).safeApprove(BAL_VAULT, type(uint256).max);
        IERC20(WETH_TOKEN).safeApprove(BAL_VAULT, 0);
        IERC20(WETH_TOKEN).safeApprove(BAL_VAULT, type(uint256).max);
        IERC20(BAL_ETH_POOL_TOKEN).safeApprove(AURABAL_PT_DEPOSIT, 0);
        IERC20(BAL_ETH_POOL_TOKEN).safeApprove(
            AURABAL_PT_DEPOSIT,
            type(uint256).max
        );
        IERC20(BAL_ETH_POOL_TOKEN).safeApprove(BAL_VAULT, 0);
        IERC20(BAL_ETH_POOL_TOKEN).safeApprove(BAL_VAULT, type(uint256).max);
    }

    /// @notice update the token to handler mapping
    function _updateRewardToken(address _token, address _handler) internal {
        rewardHandlers[_token] = _handler;
    }

    /// @notice Add a reward token and its handler
    /// @dev For tokens that should not be swapped (i.e. BAL rewards)
    ///      use address as zero handler
    /// @param _token the reward token to add
    /// @param _handler address of the contract that will sell for BAL or ETH
    function addRewardToken(
        address _token,
        address _handler
    ) external onlyOwner {
        rewardTokens.push(_token);
        _updateRewardToken(_token, _handler);
    }

    /// @notice Update the handler of a reward token
    /// @dev Used to update a handler or retire a token (set handler to address 0)
    /// @param _token the reward token to add
    /// @param _handler address of the contract that will sell for BAL or ETH
    function updateRewardToken(
        address _token,
        address _handler
    ) external onlyOwner {
        _updateRewardToken(_token, _handler);
    }

    /// @notice returns the number of reward tokens
    /// @return the number of reward tokens
    function totalRewardTokens() external view returns (uint256) {
        return rewardTokens.length;
    }

    /// @notice Query the amount currently staked
    /// @return total - the total amount of tokens staked
    function totalUnderlying() public view returns (uint256 total) {
        return auraBalStaking.balanceOf(address(this));
    }

    /// @notice Deposits underlying tokens in the staking contract
    function stake(uint256 _amount) public onlyVault {
        auraBalStaking.stake(_amount);
    }

    /// @notice Withdraw a certain amount from the staking contract
    /// @param _amount - the amount to withdraw
    /// @dev Can only be called by the vault
    function withdraw(uint256 _amount) external onlyVault {
        auraBalStaking.withdraw(_amount, false);
        IERC20(AURABAL_TOKEN).safeTransfer(vault, _amount);
    }

    /// @notice Lock or swap 20WETH-80BAL LP tokens for auraBal
    /// @param _lock - whether to lock or swap
    /// @param _minAmountOut - minimum expected amount of auraBal
    /// @return the amount of auraBal obtained from lock or swap
    function _lockOrSwap(
        bool _lock,
        uint256 _minAmountOut
    ) internal returns (uint256) {
        uint256 _bptBalance = IERC20(BAL_ETH_POOL_TOKEN).balanceOf(
            address(this)
        );
        if (_lock) {
            // if we lost to much too slippage, revert
            if (_bptBalance < _minAmountOut) {
                revert("slippage");
            }
            // lock without staking to receive auraBAL
            bptDepositor.deposit(_bptBalance, true, address(0));
            // the mint is 1:1
            return _bptBalance;
        } else {
            // if not locking we'll swap on the pool
            return _swapBptToAuraBal(_bptBalance, _minAmountOut);
        }
    }

    function _levyFees(
        uint256 _auraBalBalance,
        address _caller
    ) internal returns (uint256) {
        uint256 platformFee = IGenericVault(vault).platformFee();
        uint256 callIncentive = IGenericVault(vault).callIncentive();
        uint256 _stakingAmount = _auraBalBalance;
        // if this is the last call, no fees
        if (IGenericVault(vault).totalSupply() != 0) {
            // Deduce and pay out incentive to caller (not needed for final exit)
            if (callIncentive > 0) {
                uint256 incentiveAmount = (_auraBalBalance * callIncentive) /
                    FEE_DENOMINATOR;
                IERC20(AURABAL_TOKEN).safeTransfer(_caller, incentiveAmount);
                _stakingAmount = _stakingAmount - incentiveAmount;
            }
            // Deduce and pay platform fee
            if (platformFee > 0) {
                uint256 feeAmount = (_auraBalBalance * platformFee) /
                    FEE_DENOMINATOR;
                IERC20(AURABAL_TOKEN).safeTransfer(
                    IGenericVault(vault).platform(),
                    feeAmount
                );
                _stakingAmount = _stakingAmount - feeAmount;
            }
        }
        return _stakingAmount;
    }

    /// @notice Claim rewards and swaps them to FXS for restaking
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
        auraBalStaking.getReward();

        // process rewards
        address[] memory _rewardTokens = rewardTokens;
        for (uint256 i; i < _rewardTokens.length; ++i) {
            address _tokenHandler = rewardHandlers[_rewardTokens[i]];
            if (_tokenHandler == address(0)) {
                continue;
            }
            uint256 _tokenBalance = IERC20(_rewardTokens[i]).balanceOf(
                address(this)
            );
            if (_tokenBalance > 0) {
                IERC20(_rewardTokens[i]).safeTransfer(
                    _tokenHandler,
                    _tokenBalance
                );
                IRewardHandler(_tokenHandler).sell();
            }
        }

        uint256 _wethBalance = IERC20(WETH_TOKEN).balanceOf(address(this));
        uint256 _balBalance = IERC20(BAL_TOKEN).balanceOf(address(this));

        if (_wethBalance + _balBalance == 0) {
            return 0;
        }
        // Deposit to BLP
        _depositToBalEthPool(_balBalance, _wethBalance, 0);

        // lock or swap the LP tokens for aura BAL
        uint256 _auraBalBalance = _lockOrSwap(_lock, _minAmountOut);

        if (_auraBalBalance > 0) {
            uint256 _stakingAmount = _levyFees(_auraBalBalance, _caller);
            // stake what is left after fees
            stake(_stakingAmount);
            return _stakingAmount;
        }

        return 0;
    }

    modifier onlyVault() {
        require(vault == msg.sender, "Vault calls only");
        _;
    }
}
