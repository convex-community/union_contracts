// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

interface IHarvester {
    function sell(uint256 _amount) external;

    function setPendingOwner(address _po) external;

    function applyPendingOwner() external;

    function processRewards(uint256 _minAmountOut, bool _lock) external;
}
