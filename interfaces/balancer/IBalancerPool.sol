// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import {IBalancerVault} from "./IBalancer.sol";

interface IBalancerHelper {
    function queryJoin(
        bytes32 poolId,
        address sender,
        address recipient,
        IBalancerVault.JoinPoolRequest memory request
    ) external view returns (uint256 bptOut, uint256[] memory amountsIn);
}
