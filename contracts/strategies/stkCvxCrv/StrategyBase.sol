// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "../../../interfaces/IBasicRewards.sol";
import "../../../interfaces/ICurvePool.sol";
import "../../../interfaces/ICurveTriCrypto.sol";

contract stkCvxCrvStrategyBase {
    address private constant TRIPOOL =
        0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7;
    address private constant THREECRV_TOKEN =
        0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490;
    address private constant USDT_TOKEN =
        0xdAC17F958D2ee523a2206206994597C13D831ec7;
    address private constant TRICRYPTO =
        0xD51a44d3FaE010294C616388b506AcdA1bfAAE46;
    address private constant CVXCRV_DEPOSIT =
        0x8014595F2AB54cD7c604B00E9fb932176fDc86Ae;

    address public constant CRV_TOKEN =
        0xD533a949740bb3306d119CC777fa900bA034cd52;
    address public constant CVXCRV_TOKEN =
        0x62B9c7356A2Dc64a1969e19C23e4f579F9810Aa7;
    address public constant CVX_TOKEN =
        0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B;

    ICurvePool private tripool = ICurvePool(TRIPOOL);
    ICurveTriCrypto private tricrypto = ICurveTriCrypto(TRICRYPTO);

    receive() external payable {}
}
