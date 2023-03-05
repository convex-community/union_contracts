// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

interface IHarvester {
    function setPendingOwner(address _po) external;

    function applyPendingOwner() external;

    function processRewards(bool _forceLock) external returns (uint256);
}
