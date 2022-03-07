// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "./StrategyBase.sol";
import "../../../interfaces/IGenericVault.sol";
import "../../../interfaces/IUniV2Router.sol";
import "../../../interfaces/ICurveTriCrypto.sol";

contract CvxFxsZaps is Ownable, CvxFxsStrategyBase, ReentrancyGuard {
    using SafeERC20 for IERC20;

    address public immutable vault;

    address private constant TRICRYPTO =
        0xD51a44d3FaE010294C616388b506AcdA1bfAAE46;
    ICurveTriCrypto triCryptoSwap = ICurveTriCrypto(TRICRYPTO);

    constructor(address _vault) {
        vault = _vault;
    }

    /// @notice Change the default swap option for eth -> fxs
    /// @param _newOption - the new option to use
    function setSwapOption(SwapOption _newOption) external onlyOwner {
        SwapOption _oldOption = swapOption;
        swapOption = _newOption;
        emit OptionChanged(_oldOption, swapOption);
    }

    /// @notice Set approvals for the contracts used when swapping & staking
    function setApprovals() external {
        IERC20(CURVE_CVXFXS_FXS_LP_TOKEN).safeApprove(vault, 0);
        IERC20(CURVE_CVXFXS_FXS_LP_TOKEN).safeApprove(vault, type(uint256).max);

        IERC20(CVX_TOKEN).safeApprove(CURVE_CVX_ETH_POOL, 0);
        IERC20(CVX_TOKEN).safeApprove(CURVE_CVX_ETH_POOL, type(uint256).max);

        IERC20(FXS_TOKEN).safeApprove(CURVE_CVXFXS_FXS_POOL, 0);
        IERC20(FXS_TOKEN).safeApprove(CURVE_CVXFXS_FXS_POOL, type(uint256).max);

        IERC20(FXS_TOKEN).safeApprove(CURVE_FXS_ETH_POOL, 0);
        IERC20(FXS_TOKEN).safeApprove(CURVE_FXS_ETH_POOL, type(uint256).max);

        IERC20(CVXFXS_TOKEN).safeApprove(CURVE_CVXFXS_FXS_POOL, 0);
        IERC20(CVXFXS_TOKEN).safeApprove(
            CURVE_CVXFXS_FXS_POOL,
            type(uint256).max
        );

        IERC20(CRV_TOKEN).safeApprove(CURVE_CRV_ETH_POOL, 0);
        IERC20(CRV_TOKEN).safeApprove(CURVE_CRV_ETH_POOL, type(uint256).max);
    }

    /// @notice Deposit from FXS and/or cvxFXS
    /// @param amounts - the amounts of FXS and cvxFXS to deposit respectively
    /// @param minAmountOut - min amount of LP tokens expected
    /// @param to - address to stake on behalf of
    function depositFromUnderlyingAssets(
        uint256[2] calldata amounts,
        uint256 minAmountOut,
        address to
    ) external notToZeroAddress(to) {
        if (amounts[0] > 0) {
            IERC20(FXS_TOKEN).safeTransferFrom(
                msg.sender,
                address(this),
                amounts[0]
            );
        }
        if (amounts[1] > 0) {
            IERC20(CVXFXS_TOKEN).safeTransferFrom(
                msg.sender,
                address(this),
                amounts[1]
            );
        }
        _addAndDeposit(amounts, minAmountOut, to);
    }

    function _addAndDeposit(
        uint256[2] memory amounts,
        uint256 minAmountOut,
        address to
    ) internal {
        cvxFxsFxsSwap.add_liquidity(amounts, minAmountOut);
        IGenericVault(vault).depositAll(to);
    }

    /// @notice Deposit from FXS LP tokens, CRV and/or CVX
    /// @dev Used for users migrating their FXS + rewards from Convex
    /// @param lpTokenAmount - amount of FXS-cvxFXS LP Token from Curve
    /// @param crvAmount - amount of CRV to deposit
    /// @param cvxAmount - amount of CVX to deposit
    /// @param minAmountOut - minimum amount of LP Tokens after swapping CRV+CVX
    /// @param to - address to stake on behalf of
    function depositWithRewards(
        uint256 lpTokenAmount,
        uint256 crvAmount,
        uint256 cvxAmount,
        uint256 minAmountOut,
        address to
    ) external notToZeroAddress(to) {
        require(lpTokenAmount + crvAmount + cvxAmount > 0, "cheap");
        if (lpTokenAmount > 0) {
            IERC20(CURVE_CVXFXS_FXS_LP_TOKEN).safeTransferFrom(
                msg.sender,
                address(this),
                lpTokenAmount
            );
        }
        if (crvAmount > 0) {
            IERC20(CRV_TOKEN).safeTransferFrom(
                msg.sender,
                address(this),
                crvAmount
            );
            _swapCrvToEth(crvAmount);
        }
        if (cvxAmount > 0) {
            IERC20(CVX_TOKEN).safeTransferFrom(
                msg.sender,
                address(this),
                cvxAmount
            );
            _swapCvxToEth(cvxAmount);
        }
        if (address(this).balance > 0) {
            uint256 fxsBalance = _swapEthForFxs(
                address(this).balance,
                swapOption
            );
            cvxFxsFxsSwap.add_liquidity([fxsBalance, 0], minAmountOut);
        }
        IGenericVault(vault).depositAll(to);
    }

    /// @notice Deposit into the pounder from ETH
    /// @param minAmountOut - min amount of lp tokens expected
    /// @param to - address to stake on behalf of
    function depositFromEth(uint256 minAmountOut, address to)
        external
        payable
        notToZeroAddress(to)
    {
        require(msg.value > 0, "cheap");
        _depositFromEth(msg.value, minAmountOut, to);
    }

    /// @notice Internal function to deposit ETH to the pounder
    /// @param amount - amount of ETH
    /// @param minAmountOut - min amount of lp tokens expected
    /// @param to - address to stake on behalf of
    function _depositFromEth(
        uint256 amount,
        uint256 minAmountOut,
        address to
    ) internal {
        uint256 fxsBalance = _swapEthForFxs(amount, swapOption);
        _addAndDeposit([fxsBalance, 0], minAmountOut, to);
    }

    /// @notice Deposit into the pounder from any token via Uni interface
    /// @notice Use at your own risk
    /// @dev Zap contract needs approval for spending of inputToken
    /// @param amount - min amount of input token
    /// @param minAmountOut - min amount of cvxCRV expected
    /// @param router - address of the router to use. e.g. 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F for Sushi
    /// @param inputToken - address of the token to swap from, needs to have an ETH pair on router used
    /// @param to - address to stake on behalf of
    function depositViaUniV2EthPair(
        uint256 amount,
        uint256 minAmountOut,
        address router,
        address inputToken,
        address to
    ) external notToZeroAddress(to) {
        require(router != address(0));

        IERC20(inputToken).safeTransferFrom(msg.sender, address(this), amount);
        address[] memory _path = new address[](2);
        _path[0] = inputToken;
        _path[1] = WETH_TOKEN;

        IERC20(inputToken).safeApprove(router, 0);
        IERC20(inputToken).safeApprove(router, amount);

        IUniV2Router(router).swapExactTokensForETH(
            amount,
            1,
            _path,
            address(this),
            block.timestamp + 1
        );
        _depositFromEth(address(this).balance, minAmountOut, to);
    }

    /// @notice Remove liquidity from the Curve pool for either asset
    /// @param _amount - amount to withdraw
    /// @param _assetIndex - asset to withdraw (0: FXS, 1: cvxFXS)
    /// @param _minAmountOut - minimum amount of LP tokens expected
    /// @param _to - address to send withdrawn underlying to
    /// @return amount of underlying withdrawn
    function _claimAsUnderlying(
        uint256 _amount,
        uint256 _assetIndex,
        uint256 _minAmountOut,
        address _to
    ) internal returns (uint256) {
        return
            cvxFxsFxsSwap.remove_liquidity_one_coin(
                _amount,
                _assetIndex,
                _minAmountOut,
                false,
                _to
            );
    }

    /// @notice Retrieves a user's vault shares and withdraw all
    /// @param _amount - amount of shares to retrieve
    function _claimAndWithdraw(uint256 _amount) internal {
        IERC20(vault).safeTransferFrom(msg.sender, address(this), _amount);
        IGenericVault(vault).withdrawAll(address(this));
    }

    /// @notice Claim as either FXS or cvxFXS
    /// @param amount - amount to withdraw
    /// @param assetIndex - asset to withdraw (0: FXS, 1: cvxFXS)
    /// @param minAmountOut - minimum amount of LP tokens expected
    /// @param to - address to send withdrawn underlying to
    /// @return amount of underlying withdrawn
    function claimFromVaultAsUnderlying(
        uint256 amount,
        uint256 assetIndex,
        uint256 minAmountOut,
        address to
    ) public notToZeroAddress(to) returns (uint256) {
        _claimAndWithdraw(amount);
        return
            _claimAsUnderlying(
                IERC20(CURVE_CVXFXS_FXS_LP_TOKEN).balanceOf(address(this)),
                assetIndex,
                minAmountOut,
                to
            );
    }

    /// @notice Claim as native ETH
    /// @param amount - amount to withdraw
    /// @param minAmountOut - minimum amount of ETH expected
    /// @param to - address to send ETH to
    /// @return amount of ETH withdrawn
    function claimFromVaultAsEth(
        uint256 amount,
        uint256 minAmountOut,
        address to
    ) public nonReentrant notToZeroAddress(to) returns (uint256) {
        uint256 _ethAmount = _claimAsEth(amount);
        require(_ethAmount >= minAmountOut, "Slippage");
        (bool success, ) = to.call{value: _ethAmount}("");
        require(success, "ETH transfer failed");
        return _ethAmount;
    }

    /// @notice Withdraw as native ETH (internal)
    /// @param amount - amount to withdraw
    /// @return amount of ETH withdrawn
    function _claimAsEth(uint256 amount) public nonReentrant returns (uint256) {
        _claimAndWithdraw(amount);
        uint256 _fxsAmount = _claimAsUnderlying(
            IERC20(CURVE_CVXFXS_FXS_LP_TOKEN).balanceOf(address(this)),
            0,
            0,
            address(this)
        );
        return _swapFxsForEth(_fxsAmount, swapOption);
    }

    /// @notice Claim to any token via a univ2 router
    /// @notice Use at your own risk
    /// @param amount - amount of uFXS to unstake
    /// @param minAmountOut - min amount of output token expected
    /// @param router - address of the router to use. e.g. 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F for Sushi
    /// @param outputToken - address of the token to swap to
    /// @param to - address of the final recipient of the swapped tokens
    function claimFromVaultViaUniV2EthPair(
        uint256 amount,
        uint256 minAmountOut,
        address router,
        address outputToken,
        address to
    ) public notToZeroAddress(to) {
        require(router != address(0));
        _claimAsEth(amount);
        address[] memory _path = new address[](2);
        _path[0] = WETH_TOKEN;
        _path[1] = outputToken;
        IUniV2Router(router).swapExactETHForTokens{
            value: address(this).balance
        }(minAmountOut, _path, to, block.timestamp + 1);
    }

    /// @notice Claim as USDT via Tricrypto
    /// @param amount - the amount of uFXS to unstake
    /// @param minAmountOut - the min expected amount of USDT to receive
    /// @param to - the adress that will receive the USDT
    /// @return amount of USDT obtained
    function claimFromVaultAsUsdt(
        uint256 amount,
        uint256 minAmountOut,
        address to
    ) public notToZeroAddress(to) returns (uint256) {
        uint256 _ethAmount = _claimAsEth(amount);
        _swapEthToUsdt(_ethAmount, minAmountOut);
        uint256 _usdtAmount = IERC20(USDT_TOKEN).balanceOf(address(this));
        IERC20(USDT_TOKEN).safeTransfer(to, _usdtAmount);
        return _usdtAmount;
    }

    /// @notice swap ETH to USDT via Curve's tricrypto
    /// @param _amount - the amount of ETH to swap
    /// @param _minAmountOut - the minimum amount expected
    function _swapEthToUsdt(uint256 _amount, uint256 _minAmountOut) internal {
        triCryptoSwap.exchange{value: _amount}(
            2, // ETH
            0, // USDT
            _amount,
            _minAmountOut,
            true
        );
    }

    /// @notice Claim as CVX via CurveCVX
    /// @param amount - the amount of uFXS to unstake
    /// @param minAmountOut - the min expected amount of USDT to receive
    /// @param to - the adress that will receive the CVX
    /// @return amount of CVX obtained
    function claimFromVaultAsUsdt(
        uint256 amount,
        uint256 minAmountOut,
        address to
    ) public notToZeroAddress(to) returns (uint256) {
        uint256 _ethAmount = _claimAsEth(amount);
        uint256 _cvxAmount = _swapEthToCvx(_ethAmount, minAmountOut);
        IERC20(CVX_TOKEN).safeTransfer(to, _cvxAmount);
        return _cvxAmount;
    }

    /// @notice Execute calls on behalf of contract
    /// (for instance to retrieve locked tokens)
    function execute(
        address _to,
        uint256 _value,
        bytes calldata _data
    ) external onlyOwner returns (bool, bytes memory) {
        (bool success, bytes memory result) = _to.call{value: _value}(_data);
        return (success, result);
    }

    modifier notToZeroAddress(address _to) {
        require(_to != address(0), "Invalid address!");
        _;
    }
}
