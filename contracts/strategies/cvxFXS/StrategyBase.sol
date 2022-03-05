// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "../../../interfaces/ICurveV2Pool.sol";
import "../../../interfaces/ICurveFactoryPool.sol";
import "../../../interfaces/IBasicRewards.sol";
import "../../../interfaces/IBooster.sol";
import "../../../interfaces/IUniV3Router.sol";
import "../../../interfaces/IUniV2Router.sol";

contract CvxFxsStrategyBase {
    address public constant CVXFXS_STAKING_CONTRACT =
        0xf27AFAD0142393e4b3E5510aBc5fe3743Ad669Cb;
    address public constant BOOSTER =
        0xF403C135812408BFbE8713b5A23a04b3D48AAE31;
    address public constant CURVE_CRV_ETH_POOL =
        0x8301AE4fc9c624d1D396cbDAa1ed877821D7C511;
    address public constant CURVE_CVX_ETH_POOL =
        0xB576491F1E6e5E62f1d8F26062Ee822B40B0E0d4;
    address public constant CURVE_FXS_ETH_POOL =
        0x941Eb6F616114e4Ecaa85377945EA306002612FE;
    address public constant CURVE_CVXFXS_FXS_POOL =
        0xd658A338613198204DCa1143Ac3F01A722b5d94A;
    address public constant UNISWAP_ROUTER =
        0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    address public constant UNIV3_ROUTER =
        0xE592427A0AEce92De3Edee1F18E0157C05861564;

    address public constant CRV_TOKEN =
        0xD533a949740bb3306d119CC777fa900bA034cd52;
    address public constant CVXFXS_TOKEN =
        0xFEEf77d3f69374f66429C91d732A244f074bdf74;
    address public constant FXS_TOKEN =
        0x3432B6A60D23Ca0dFCa7761B7ab56459D9C964D0;
    address public constant CVX_TOKEN =
        0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B;
    address public constant WETH_TOKEN =
        0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    address public constant CURVE_CVXFXS_FXS_LP_TOKEN =
        0xF3A43307DcAFa93275993862Aae628fCB50dC768;
    address public constant USDT_TOKEN =
        0xdAC17F958D2ee523a2206206994597C13D831ec7;
    address public constant FRAX_TOKEN =
        0x853d955aCEf822Db058eb8505911ED77F175b99e;

    uint256 public constant CRVETH_ETH_INDEX = 0;
    uint256 public constant CRVETH_CRV_INDEX = 1;
    uint256 public constant CVXETH_ETH_INDEX = 0;
    uint256 public constant CVXETH_CVX_INDEX = 1;

    // The swap strategy to use when going eth -> fxs
    enum SwapOption {
        Curve,
        Uniswap,
        Unistables
    }
    SwapOption public swapOption = SwapOption.Curve;
    event OptionChanged(SwapOption oldOption, SwapOption newOption);

    IBasicRewards cvxFxsStaking = IBasicRewards(CVXFXS_STAKING_CONTRACT);
    ICurveV2Pool cvxEthSwap = ICurveV2Pool(CURVE_CVX_ETH_POOL);
    IBooster booster = IBooster(BOOSTER);
    ICurveV2Pool crvEthSwap = ICurveV2Pool(CURVE_CRV_ETH_POOL);
    ICurveV2Pool fxsEthSwap = ICurveV2Pool(CURVE_FXS_ETH_POOL);
    ICurveV2Pool cvxFxsFxsSwap = ICurveV2Pool(CURVE_CVXFXS_FXS_POOL);

    /// @notice Swap CRV for native ETH on Curve
    /// @param amount - amount to swap
    /// @return amount of ETH obtained after the swap
    function _swapCrvToEth(uint256 amount) internal returns (uint256) {
        return _crvToEth(amount, 0);
    }

    /// @notice Swap CRV for native ETH on Curve
    /// @param amount - amount to swap
    /// @param minAmountOut - minimum expected amount of output tokens
    /// @return amount of ETH obtained after the swap
    function _swapCrvToEth(uint256 amount, uint256 minAmountOut)
        internal
        returns (uint256)
    {
        return _crvToEth(amount, minAmountOut);
    }

    /// @notice Swap CRV for native ETH on Curve
    /// @param amount - amount to swap
    /// @param minAmountOut - minimum expected amount of output tokens
    /// @return amount of ETH obtained after the swap
    function _crvToEth(uint256 amount, uint256 minAmountOut)
        internal
        returns (uint256)
    {
        return
            crvEthSwap.exchange_underlying{value: 0}(
                CRVETH_CRV_INDEX,
                CRVETH_ETH_INDEX,
                amount,
                minAmountOut
            );
    }

    /// @notice Swap native ETH for CRV on Curve
    /// @param amount - amount to swap
    /// @return amount of CRV obtained after the swap
    function _swapEthToCrv(uint256 amount) internal returns (uint256) {
        return _ethToCrv(amount, 0);
    }

    /// @notice Swap native ETH for CRV on Curve
    /// @param amount - amount to swap
    /// @param minAmountOut - minimum expected amount of output tokens
    /// @return amount of CRV obtained after the swap
    function _swapEthToCrv(uint256 amount, uint256 minAmountOut)
        internal
        returns (uint256)
    {
        return _ethToCrv(amount, minAmountOut);
    }

    /// @notice Swap native ETH for CRV on Curve
    /// @param amount - amount to swap
    /// @param minAmountOut - minimum expected amount of output tokens
    /// @return amount of CRV obtained after the swap
    function _ethToCrv(uint256 amount, uint256 minAmountOut)
        internal
        returns (uint256)
    {
        return
            crvEthSwap.exchange_underlying{value: amount}(
                CRVETH_ETH_INDEX,
                CRVETH_CRV_INDEX,
                amount,
                minAmountOut
            );
    }

    /// @notice Swap native ETH for CVX on Curve
    /// @param amount - amount to swap
    /// @return amount of CRV obtained after the swap
    function _swapEthToCvx(uint256 amount) internal returns (uint256) {
        return _ethToCvx(amount, 0);
    }

    /// @notice Swap native ETH for CVX on Curve
    /// @param amount - amount to swap
    /// @param minAmountOut - minimum expected amount of output tokens
    /// @return amount of CRV obtained after the swap
    function _swapEthToCvx(uint256 amount, uint256 minAmountOut)
        internal
        returns (uint256)
    {
        return _ethToCvx(amount, minAmountOut);
    }

    /// @notice Swap CVX for native ETH on Curve
    /// @param amount - amount to swap
    /// @return amount of ETH obtained after the swap
    function _swapCvxToEth(uint256 amount) internal returns (uint256) {
        return _cvxToEth(amount, 0);
    }

    /// @notice Swap CVX for native ETH on Curve
    /// @param amount - amount to swap
    /// @param minAmountOut - minimum expected amount of output tokens
    /// @return amount of ETH obtained after the swap
    function _swapCvxToEth(uint256 amount, uint256 minAmountOut)
        internal
        returns (uint256)
    {
        return _cvxToEth(amount, minAmountOut);
    }

    /// @notice Swap native ETH for CVX on Curve
    /// @param amount - amount to swap
    /// @param minAmountOut - minimum expected amount of output tokens
    /// @return amount of CRV obtained after the swap
    function _ethToCvx(uint256 amount, uint256 minAmountOut)
        internal
        returns (uint256)
    {
        return
            cvxEthSwap.exchange_underlying{value: amount}(
                CVXETH_ETH_INDEX,
                CVXETH_CVX_INDEX,
                amount,
                minAmountOut
            );
    }

    /// @notice Swap native CVX for ETH on Curve
    /// @param amount - amount to swap
    /// @param minAmountOut - minimum expected amount of output tokens
    /// @return amount of ETH obtained after the swap
    function _cvxToEth(uint256 amount, uint256 minAmountOut)
        internal
        returns (uint256)
    {
        return
            cvxEthSwap.exchange_underlying{value: 0}(
                1,
                0,
                amount,
                minAmountOut
            );
    }

    /// @notice Swap native ETH for FXS via different routes
    /// @param _ethAmount - amount to swap
    /// @param _option - the option to use when swapping
    function _swapEthForFxs(uint256 _ethAmount, SwapOption _option)
        internal
        returns (uint256 _swapped)
    {
        if (_option == SwapOption.Curve) {
            return
                fxsEthSwap.exchange_underlying{value: _ethAmount}(
                    0,
                    1,
                    _ethAmount,
                    0
                );
        } else if (_option == SwapOption.Uniswap) {
            IUniV3Router.ExactInputSingleParams memory _params = IUniV3Router
                .ExactInputSingleParams(
                    WETH_TOKEN,
                    FXS_TOKEN,
                    10000,
                    address(this),
                    block.timestamp + 1,
                    _ethAmount,
                    1,
                    0
                );
            return
                IUniV3Router(UNIV3_ROUTER).exactInputSingle{value: _ethAmount}(
                    _params
                );
        } else {
            uint24 fee = 500;
            IUniV3Router.ExactInputParams memory _params = IUniV3Router
                .ExactInputParams(
                    abi.encodePacked(
                        WETH_TOKEN,
                        fee,
                        USDT_TOKEN,
                        fee,
                        FRAX_TOKEN
                    ),
                    address(this),
                    block.timestamp + 1,
                    _ethAmount,
                    0
                );

            uint256 _fraxAmount = IUniV3Router(UNIV3_ROUTER).exactInput{
                value: _ethAmount
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
            return amounts[0];
        }
    }

    receive() external payable {}
}
