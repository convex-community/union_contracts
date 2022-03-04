// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

interface IQuoter {
    function quoteExactInputSingle(
        address tokenIn,
        address tokenOut,
        uint24 fee,
        uint256 amountIn,
        uint160 sqrtPriceLimitX96
    ) external view returns (uint256 amountOut);

    function quoteExactInput(bytes memory path, uint256 amountIn) external view returns (uint256 amountOut);
}
