// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

interface IVirtualBalanceRewardPool {
    function earned(address account) external view returns (uint256);
}
