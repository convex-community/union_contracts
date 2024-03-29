// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

interface IStrategyOracle {
    function harvest(address _caller) external returns (uint256 harvested);

    function totalUnderlying() external view returns (uint256 total);

    function stake(uint256 _amount) external;

    function withdraw(uint256 _amount) external;

    function setApprovals() external;
}
