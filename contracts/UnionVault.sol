// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "../interfaces/ICurvePool.sol";
import "../interfaces/ICurveTriCrypto.sol";
import "../interfaces/ICvxCrvDeposit.sol";
import "../interfaces/ICvxMining.sol";
import "../interfaces/IVirtualBalanceRewardPool.sol";
import "./ClaimZaps.sol";

contract UnionVault is ClaimZaps, ERC20, Ownable {
    using SafeERC20 for IERC20;

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
    address public platform = 0x9Bc7c6ad7E7Cf3A6fCB58fb21e27752AC1e53f99;

    uint256 public withdrawalPenalty = 100;
    uint256 public constant MAX_WITHDRAWAL_PENALTY = 150;
    uint256 public platformFee = 500;
    uint256 public constant MAX_PLATFORM_FEE = 2000;
    uint256 public callIncentive = 500;
    uint256 public constant MAX_CALL_INCENTIVE = 500;
    uint256 public constant FEE_DENOMINATOR = 10000;

    ICurvePool private tripool = ICurvePool(TRIPOOL);
    ICurveTriCrypto private tricrypto = ICurveTriCrypto(TRICRYPTO);

    event Harvest(address indexed caller, uint256 amount);
    event Stake(uint256 amount);
    event Unstake(address indexed user, uint256 amount);

    constructor()
        ERC20(
            string(abi.encodePacked("Unionized cvxCRV")),
            string(abi.encodePacked("uCRV"))
        )
    {}

    /// @notice Set approvals for the contracts used when swapping & staking
    function setApprovals() external onlyOwner {
        IERC20(THREECRV_TOKEN).safeApprove(TRIPOOL, 0);
        IERC20(THREECRV_TOKEN).safeApprove(TRIPOOL, type(uint256).max);

        IERC20(CVX_TOKEN).safeApprove(CURVE_CVX_ETH_POOL, 0);
        IERC20(CVX_TOKEN).safeApprove(CURVE_CVX_ETH_POOL, type(uint256).max);

        IERC20(USDT_TOKEN).safeApprove(TRICRYPTO, 0);
        IERC20(USDT_TOKEN).safeApprove(TRICRYPTO, type(uint256).max);

        IERC20(CRV_TOKEN).safeApprove(CVXCRV_DEPOSIT, 0);
        IERC20(CRV_TOKEN).safeApprove(CVXCRV_DEPOSIT, type(uint256).max);

        IERC20(CRV_TOKEN).safeApprove(CURVE_CVXCRV_CRV_POOL, 0);
        IERC20(CRV_TOKEN).safeApprove(CURVE_CVXCRV_CRV_POOL, type(uint256).max);

        _setApprovals();
    }

    /// @notice Updates the withdrawal penalty
    /// @param _penalty - the amount of the new penalty (in BIPS)
    function setWithdrawalPenalty(uint256 _penalty) external onlyOwner {
        require(_penalty <= MAX_WITHDRAWAL_PENALTY);
        withdrawalPenalty = _penalty;
    }

    /// @notice Updates the caller incentive for harvests
    /// @param _incentive - the amount of the new incentive (in BIPS)
    function setCallIncentive(uint256 _incentive) external onlyOwner {
        require(_incentive <= MAX_CALL_INCENTIVE);
        callIncentive = _incentive;
    }

    /// @notice Updates the part of yield redirected to the platform
    /// @param _fee - the amount of the new platform fee (in BIPS)
    function setPlatformFee(uint256 _fee) external onlyOwner {
        require(_fee <= MAX_PLATFORM_FEE);
        platformFee = _fee;
    }

    /// @notice Updates the address to which platform fees are paid out
    /// @param _platform - the new platform wallet address
    function setPlatform(address _platform) external onlyOwner {
        require(_platform != address(0));
        platform = _platform;
    }

    /// @notice Query the amount currently staked
    /// @return total - the total amount of tokens staked
    function totalHoldings() public view returns (uint256 total) {
        return cvxCrvStaking.balanceOf(address(this));
    }

    /// @notice Query the total amount of currently claimable CRV
    /// @return total - the total amount of CRV claimable
    function outstandingCrvRewards() public view returns (uint256 total) {
        return cvxCrvStaking.earned(address(this));
    }

    /// @notice Query the total amount of currently claimable CVX
    /// @return total - the total amount of CVX claimable
    function outstandingCvxRewards() external view returns (uint256 total) {
        return
            ICvxMining(CVX_MINING_LIB).ConvertCrvToCvx(outstandingCrvRewards());
    }

    /// @notice Query the total amount of currently claimable 3CRV
    /// @return total - the total amount of 3CRV claimable
    function outstanding3CrvRewards() external view returns (uint256 total) {
        return
            IVirtualBalanceRewardPool(THREE_CRV_REWARDS).earned(address(this));
    }

    /// @notice Returns the amount of cvxCRV a user can claim
    /// @param user - address whose claimable amount to query
    /// @return amount - claimable amount
    /// @dev Does not account for penalties and fees
    function balanceOfUnderlying(address user)
        external
        view
        returns (uint256 amount)
    {
        require(totalSupply() > 0, "No users");
        return ((balanceOf(user) * totalHoldings()) / totalSupply());
    }

    /// @notice Returns the address of underlying token
    function underlying() external view returns (address underlying) {
        return CVXCRV_TOKEN;
    }

    /// @notice Claim rewards and swaps them to cvxCrv for restaking
    /// @dev Can be called by anyone against an incentive in cvxCrv
    function harvest() public {
        // claim rewards
        cvxCrvStaking.getReward();

        // sell CVX rewards for ETH
        uint256 _cvxAmount = IERC20(CVX_TOKEN).balanceOf(address(this));
        if (_cvxAmount > 0) {
            cvxEthSwap.exchange_underlying{value: 0}(
                CVXETH_CVX_INDEX,
                CVXETH_ETH_INDEX,
                _cvxAmount,
                0
            );
        }

        // pull 3crv out as USDT, swap for ETH
        uint256 _threeCrvBalance = IERC20(THREECRV_TOKEN).balanceOf(
            address(this)
        );
        if (_threeCrvBalance > 0) {
            tripool.remove_liquidity_one_coin(_threeCrvBalance, 2, 0);

            uint256 _usdtBalance = IERC20(USDT_TOKEN).balanceOf(address(this));
            if (_usdtBalance > 0) {
                tricrypto.exchange(0, 2, _usdtBalance, 0, true);
            }
        }
        // swap everything to CRV
        uint256 _crvBalance = IERC20(CRV_TOKEN).balanceOf(address(this));
        uint256 _ethBalance = address(this).balance;
        if (_ethBalance > 0) {
            _crvBalance += _swapEthToCrv(address(this).balance);
        }
        if (_crvBalance > 0) {
            uint256 _quote = crvCvxCrvSwap.get_dy(
                CVXCRV_CRV_INDEX,
                CVXCRV_CVXCRV_INDEX,
                _crvBalance
            );
            // swap on Curve if there is a premium for doing so
            if (_quote > _crvBalance) {
                _swapCrvToCvxCrv(_crvBalance, address(this));
            }
            // otherwise deposit & lock
            else {
                ICvxCrvDeposit(CVXCRV_DEPOSIT).deposit(_crvBalance, true);
            }
        }
        uint256 _cvxCrvBalance = IERC20(CVXCRV_TOKEN).balanceOf(address(this));

        emit Harvest(msg.sender, _cvxCrvBalance);

        // if this is the last call, no restake & no fees
        if (totalSupply() == 0) {
            return;
        }

        if (_cvxCrvBalance > 0) {
            uint256 _stakingAmount = _cvxCrvBalance;
            // Deduce and pay out incentive to caller (not needed for final exit)
            if (callIncentive > 0) {
                uint256 incentiveAmount = (_cvxCrvBalance * callIncentive) /
                    FEE_DENOMINATOR;
                IERC20(CVXCRV_TOKEN).safeTransfer(msg.sender, incentiveAmount);
                _stakingAmount = _stakingAmount - incentiveAmount;
            }
            // Deduce and pay platform fee
            if (platformFee > 0) {
                uint256 feeAmount = (_cvxCrvBalance * platformFee) /
                    FEE_DENOMINATOR;
                IERC20(CVXCRV_TOKEN).safeTransfer(platform, feeAmount);
                _stakingAmount = _stakingAmount - feeAmount;
            }
            _stake(_stakingAmount);
        }
    }

    /// @notice Stakes a certain amount of cvxCrv
    /// @param _amount - amount of cvxCrv to stake
    function _stake(uint256 _amount) internal {
        cvxCrvStaking.stake(_amount);
        emit Stake(_amount);
    }

    /// @notice Deposit user funds in the autocompounder and mints tokens
    /// representing user's share of the pool in exchange
    /// @param _to - the address that will receive the shares
    /// @param _amount - the amount of cvxCrv to deposit
    /// @return shares - the amount of shares issued
    function deposit(address _to, uint256 _amount)
        public
        notToZeroAddress(_to)
        returns (uint256 shares)
    {
        require(_amount > 0, "Deposit too small");

        uint256 _before = totalHoldings();
        IERC20(CVXCRV_TOKEN).safeTransferFrom(
            msg.sender,
            address(this),
            _amount
        );
        _stake(_amount);

        // Issues shares in proportion of deposit to pool amount
        uint256 shares = 0;
        if (totalSupply() == 0) {
            shares = _amount;
        } else {
            shares = (_amount * totalSupply()) / _before;
        }
        _mint(_to, shares);
        return shares;
    }

    /// @notice Deposit all of user's cvxCRV balance
    /// @param _to - the address that will receive the shares
    /// @return shares - the amount of shares issued
    function depositAll(address _to) external returns (uint256 shares) {
        return deposit(_to, IERC20(CVXCRV_TOKEN).balanceOf(msg.sender));
    }

    /// @notice Unstake cvxCrv in proportion to the amount of shares sent
    /// @param _shares - the number of shares sent
    /// @return _withdrawable - the withdrawable cvxCrv amount
    function _withdraw(uint256 _shares)
        internal
        returns (uint256 _withdrawable)
    {
        require(totalSupply() > 0);
        // Computes the amount withdrawable based on the number of shares sent
        uint256 amount = (_shares * totalHoldings()) / totalSupply();
        // Burn the shares before retrieving tokens
        _burn(msg.sender, _shares);
        _withdrawable = amount;
        // If user is last to withdraw, harvest before exit
        if (totalSupply() == 0) {
            harvest();
            cvxCrvStaking.withdraw(totalHoldings(), false);
            _withdrawable = IERC20(CVXCRV_TOKEN).balanceOf(address(this));
        }
        // Otherwise compute share and unstake
        else {
            // Substract a small withdrawal fee to prevent users "timing"
            // the harvests. The fee stays staked and is therefore
            // redistributed to all remaining participants.
            uint256 _penalty = (_withdrawable * withdrawalPenalty) /
                FEE_DENOMINATOR;
            _withdrawable = _withdrawable - _penalty;
            cvxCrvStaking.withdraw(_withdrawable, false);
        }
        return _withdrawable;
    }

    /// @notice Unstake cvxCrv in proportion to the amount of shares sent
    /// @param _to - address to send cvxCrv to
    /// @param _shares - the number of shares sent
    /// @return withdrawn - the amount of cvxCRV returned to the user
    function withdraw(address _to, uint256 _shares)
        public
        notToZeroAddress(_to)
        returns (uint256 withdrawn)
    {
        // Withdraw requested amount of cvxCrv
        uint256 _withdrawable = _withdraw(_shares);
        // And sends back cvxCrv to user
        IERC20(CVXCRV_TOKEN).safeTransfer(_to, _withdrawable);
        emit Unstake(_to, _withdrawable);
        return _withdrawable;
    }

    /// @notice Withdraw all of a users' position as cvxCRV
    /// @param _to - address to send cvxCrv to
    /// @return withdrawn - the amount of cvxCRV returned to the user
    function withdrawAll(address _to)
        external
        notToZeroAddress(_to)
        returns (uint256 withdrawn)
    {
        return withdraw(_to, balanceOf(msg.sender));
    }

    /// @notice Zap function to withdraw as another token
    /// @param _to - address to send cvxCrv to
    /// @param _shares - the number of shares sent
    /// @param option - what to swap to
    function withdrawAs(
        address _to,
        uint256 _shares,
        Option option
    ) external notToZeroAddress(_to) {
        uint256 _withdrawn = _withdraw(_shares);
        _claimAs(_to, _withdrawn, option);
    }

    /// @notice Zap function to withdraw all shares to another token
    /// @param _to - address to send cvxCrv to
    /// @param option - what to swap to
    function withdrawAllAs(address _to, Option option)
        external
        notToZeroAddress(_to)
    {
        uint256 _withdrawn = _withdraw(balanceOf(msg.sender));
        _claimAs(_to, _withdrawn, option);
    }

    /// @notice Zap function to withdraw as another token
    /// @param _to - address to send cvxCrv to
    /// @param _shares - the number of shares sent
    /// @param option - what to swap to
    /// @param minAmountOut - minimum desired amount of output token
    function withdrawAs(
        address _to,
        uint256 _shares,
        Option option,
        uint256 minAmountOut
    ) external notToZeroAddress(_to) {
        uint256 _withdrawn = _withdraw(_shares);
        _claimAs(_to, _withdrawn, option, minAmountOut);
    }

    /// @notice Zap function to withdraw all shares to another token
    /// @param _to - address to send cvxCrv to
    /// @param option - what to swap to
    /// @param minAmountOut - minimum desired amount of output token
    function withdrawAllAs(
        address _to,
        Option option,
        uint256 minAmountOut
    ) external notToZeroAddress(_to) {
        uint256 _withdrawn = _withdraw(balanceOf(msg.sender));
        _claimAs(_to, _withdrawn, option, minAmountOut);
    }

    receive() external payable {}

    modifier notToZeroAddress(address _to) {
        require(_to != address(0), "Receiver!");
        _;
    }
}
