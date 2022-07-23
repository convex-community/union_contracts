// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

interface IBalancerPool {
    function queryJoin(
        bytes32 poolId,
        address sender,
        address recipient,
        uint256[] memory balances,
        uint256 lastChangeBlock,
        uint256 protocolSwapFeePercentage,
        bytes memory userData
    ) external view returns (uint256 bptOut, uint256[] memory amountsIn);
}
