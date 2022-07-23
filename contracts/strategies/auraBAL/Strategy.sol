// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "../../../interfaces/IGenericVault.sol";
import "../../../interfaces/IStrategy.sol";
import "./StrategyBase.sol";

contract AuraBalStrategy is Ownable, AuraBalStrategyBase, IStrategy {
    using SafeERC20 for IERC20;

    address public immutable vault;

    uint256 public constant FEE_DENOMINATOR = 10000;

    constructor(address _vault) {
        vault = _vault;
    }

    /// @notice Set approvals for the contracts used when swapping & staking
    function setApprovals() external {
        IERC20(AURABAL_TOKEN).safeApprove(AURABAL_STAKING, 0);
        IERC20(AURABAL_TOKEN).safeApprove(AURABAL_STAKING, type(uint256).max);
        IERC20(AURA_TOKEN).safeApprove(BAL_VAULT, 0);
        IERC20(AURA_TOKEN).safeApprove(BAL_VAULT, type(uint256).max);
        IERC20(BBUSD_TOKEN).safeApprove(BAL_VAULT, 0);
        IERC20(BBUSD_TOKEN).safeApprove(BAL_VAULT, type(uint256).max);
        IERC20(BAL_TOKEN).safeApprove(BAL_VAULT, 0);
        IERC20(BAL_TOKEN).safeApprove(BAL_VAULT, type(uint256).max);
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

        // sell AURA rewards for WETH
        uint256 _auraBalance = IERC20(AURA_TOKEN).balanceOf(address(this));
        if (_auraBalance > 0) {
            _swapAuraToWEth(_auraBalance, 0);
        }

        // sell bb-usd rewards for WETH
        uint256 _bbusdBalance = IERC20(BBUSD_TOKEN).balanceOf(address(this));
        if (_bbusdBalance > 0) {
            _swapBbUsdToWEth(_bbusdBalance);
        }

        uint256 _wethBalance = IERC20(WETH_TOKEN).balanceOf(address(this));
        uint256 _balBalance = IERC20(BAL_TOKEN).balanceOf(address(this));

        // Deposit to BLP
        _depositToBalEthPool(_balBalance, _wethBalance, 0);

        uint256 _bptBalance = IERC20(BAL_ETH_POOL_TOKEN).balanceOf(
            address(this)
        );

        uint256 _stakingAmount = _bptBalance;

        if (_bptBalance > 0) {
            // if this is the last call, no fees
            if (IGenericVault(vault).totalSupply() != 0) {
                // Deduce and pay out incentive to caller (not needed for final exit)
                if (IGenericVault(vault).callIncentive() > 0) {
                    uint256 incentiveAmount = (_bptBalance *
                        IGenericVault(vault).callIncentive()) / FEE_DENOMINATOR;
                    IERC20(BAL_ETH_POOL_TOKEN).safeTransfer(
                        _caller,
                        incentiveAmount
                    );
                    _stakingAmount = _stakingAmount - incentiveAmount;
                }
                // Deduce and pay platform fee
                if (IGenericVault(vault).platformFee() > 0) {
                    uint256 feeAmount = (_bptBalance *
                        IGenericVault(vault).platformFee()) / FEE_DENOMINATOR;
                    IERC20(BAL_ETH_POOL_TOKEN).safeTransfer(
                        IGenericVault(vault).platform(),
                        feeAmount
                    );
                    _stakingAmount = _stakingAmount - feeAmount;
                }
            }
            // stake and lock
            bptDepositor.deposit(_stakingAmount, true);
        }

        return _stakingAmount;
    }

    modifier onlyVault() {
        require(vault == msg.sender, "Vault calls only");
        _;
    }
}
