// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "../../interfaces/ICurveV2Pool.sol";
import "../../interfaces/ICurveFactoryPool.sol";
import "../../interfaces/IBasicRewards.sol";
import "../../interfaces/IWETH.sol";
import "../../interfaces/IUniV3Router.sol";
import "../../interfaces/IUniV2Router.sol";

contract FXSSwapper is Ownable {
    using SafeERC20 for IERC20;

    address public constant CURVE_FXS_ETH_POOL =
        0x941Eb6F616114e4Ecaa85377945EA306002612FE;
    address public constant FXS_TOKEN =
        0x3432B6A60D23Ca0dFCa7761B7ab56459D9C964D0;
    address public constant UNISWAP_ROUTER =
        0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    address public constant UNIV3_ROUTER =
        0xE592427A0AEce92De3Edee1F18E0157C05861564;
    address public constant WETH_TOKEN =
        0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    address public constant USDT_TOKEN =
        0xdAC17F958D2ee523a2206206994597C13D831ec7;
    address public constant USDC_TOKEN =
        0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48;
    address public constant FRAX_TOKEN =
        0x853d955aCEf822Db058eb8505911ED77F175b99e;
    address public constant vault;

    ICurveV2Pool fxsEthSwap = ICurveV2Pool(CURVE_FXS_ETH_POOL);
    // The swap strategy to use when going eth -> fxs
    enum SwapOption {
        Curve,
        Uniswap,
        Unistables
    }
    SwapOption public swapOption = SwapOption.Unistables;

    constructor(address _vault) {
        require(_vault != address(0));
        vault = _vault;
    }

    /// @notice Change the vault authorized to call buy and sell functions
    /// @param _vault - address of the new vault
    function updateVault(address _vault) external onlyOwner {
        require(_vault != address(0));
        vault = _vault;
    }

    /// @notice Change the swap option for FXS/ETH
    /// @param _option - the new swap option
    function updateOption(SwapOption _option) external onlyOwner {
        swapOption = _option;
    }

    /// @notice Buy FXS with ETH
    /// @param amount - amount of ETH to buy with
    /// @dev ETH must have been sent to the contract prior
    function buy(uint256 amount) external onlyVault {
        uint256 _received = _swapEthForFxs(amount, swapOption);
        IERC20(FXS_TOKEN).safeTransfer(vault, _received);
    }

    /// @notice Sell FXS for ETH
    /// @param amount - amount of FXS to sell
    /// @dev FXS must have been sent to the contract prior
    function sell(uint256 amount) external onlyVault {
        uint256 _received = _swapFxsForEth(amount, swapOption);
        (bool success, ) = vault.call{value: _received}("");
        require(success, "ETH transfer failed");
    }

    /// @notice Swap native ETH for FXS via different routes
    /// @param _ethAmount - amount to swap
    /// @param _option - the option to use when swapping
    /// @return amount of FXS obtained after the swap
    function _swapEthForFxs(uint256 _ethAmount, SwapOption _option)
        internal
        returns (uint256)
    {
        return _swapEthFxs(_ethAmount, _option, true);
    }

    /// @notice Swap FXS for native ETH via different routes
    /// @param _fxsAmount - amount to swap
    /// @param _option - the option to use when swapping
    /// @return amount of ETH obtained after the swap
    function _swapFxsForEth(uint256 _fxsAmount, SwapOption _option)
        internal
        returns (uint256)
    {
        return _swapEthFxs(_fxsAmount, _option, false);
    }

    /// @notice Swap ETH<->FXS on Curve
    /// @param _amount - amount to swap
    /// @param _ethToFxs - whether to swap from eth to fxs or the inverse
    /// @return amount of token obtained after the swap
    function _curveEthFxsSwap(uint256 _amount, bool _ethToFxs)
        internal
        returns (uint256)
    {
        return
            fxsEthSwap.exchange_underlying{value: _ethToFxs ? _amount : 0}(
                _ethToFxs ? 0 : 1,
                _ethToFxs ? 1 : 0,
                _amount,
                0
            );
    }

    /// @notice Swap ETH<->FXS on UniV3 FXSETH pool
    /// @param _amount - amount to swap
    /// @param _ethToFxs - whether to swap from eth to fxs or the inverse
    /// @return amount of token obtained after the swap
    function _uniV3EthFxsSwap(uint256 _amount, bool _ethToFxs)
        internal
        returns (uint256)
    {
        IUniV3Router.ExactInputSingleParams memory _params = IUniV3Router
            .ExactInputSingleParams(
                _ethToFxs ? WETH_TOKEN : FXS_TOKEN,
                _ethToFxs ? FXS_TOKEN : WETH_TOKEN,
                10000,
                address(this),
                block.timestamp + 1,
                _amount,
                1,
                0
            );

        uint256 _receivedAmount = IUniV3Router(UNIV3_ROUTER).exactInputSingle{
            value: _ethToFxs ? _amount : 0
        }(_params);
        if (!_ethToFxs) {
            IWETH(WETH_TOKEN).withdraw(_receivedAmount);
        }
        return _receivedAmount;
    }

    /// @notice Swap ETH->FXS on UniV3 via stable pair
    /// @param _amount - amount to swap
    /// @return amount of token obtained after the swap
    function _uniStableEthToFxsSwap(uint256 _amount)
        internal
        returns (uint256)
    {
        uint24 fee = 500;
        IUniV3Router.ExactInputParams memory _params = IUniV3Router
            .ExactInputParams(
                abi.encodePacked(WETH_TOKEN, fee, USDC_TOKEN, fee, FRAX_TOKEN),
                address(this),
                block.timestamp + 1,
                _amount,
                0
            );

        uint256 _fraxAmount = IUniV3Router(UNIV3_ROUTER).exactInput{
            value: _amount
        }(_params);
        address[] memory _path = new address[](2);
        _path[0] = FRAX_TOKEN;
        _path[1] = FXS_TOKEN;
        uint256[] memory amounts = IUniV2Router(UNISWAP_ROUTER)
            .swapExactTokensForTokens(
                _fraxAmount,
                1,
                _path,
                address(this),
                block.timestamp + 1
            );
        return amounts[1];
    }

    /// @notice Swap FXS->ETH on UniV3 via stable pair
    /// @param _amount - amount to swap
    /// @return amount of token obtained after the swap
    function _uniStableFxsToEthSwap(uint256 _amount)
        internal
        returns (uint256)
    {
        address[] memory _path = new address[](2);
        _path[0] = FXS_TOKEN;
        _path[1] = FRAX_TOKEN;
        uint256[] memory amounts = IUniV2Router(UNISWAP_ROUTER)
            .swapExactTokensForTokens(
                _amount,
                1,
                _path,
                address(this),
                block.timestamp + 1
            );

        uint256 _fraxAmount = amounts[1];
        uint24 fee = 500;

        IUniV3Router.ExactInputParams memory _params = IUniV3Router
            .ExactInputParams(
                abi.encodePacked(FRAX_TOKEN, fee, USDC_TOKEN, fee, WETH_TOKEN),
                address(this),
                block.timestamp + 1,
                _fraxAmount,
                0
            );

        uint256 _ethAmount = IUniV3Router(UNIV3_ROUTER).exactInput{value: 0}(
            _params
        );
        IWETH(WETH_TOKEN).withdraw(_ethAmount);
        return _ethAmount;
    }

    /// @notice Swap native ETH for FXS via different routes
    /// @param _amount - amount to swap
    /// @param _option - the option to use when swapping
    /// @param _ethToFxs - whether to swap from eth to fxs or the inverse
    /// @return amount of token obtained after the swap
    function _swapEthFxs(
        uint256 _amount,
        SwapOption _option,
        bool _ethToFxs
    ) internal returns (uint256) {
        if (_option == SwapOption.Curve) {
            return _curveEthFxsSwap(_amount, _ethToFxs);
        } else if (_option == SwapOption.Uniswap) {
            return _uniV3EthFxsSwap(_amount, _ethToFxs);
        } else {
            return
                _ethToFxs
                    ? _uniStableEthToFxsSwap(_amount)
                    : _uniStableFxsToEthSwap(_amount);
        }
    }

    receive() external payable {}

    modifier onlyVault() {
        require(msg.sender == vault, "Vault only");
    }
}
