// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

interface IHarvester {
    function setPendingOwner(address _po) external;

    function applyPendingOwner() external;

    function processRewards(uint256 _minAmountOut, bool _lock)
        external
        returns (uint256);
}
