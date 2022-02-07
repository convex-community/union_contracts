// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

interface IBooster {
    function depositAll(uint256 _pid, bool _stake) external returns (bool);
}
