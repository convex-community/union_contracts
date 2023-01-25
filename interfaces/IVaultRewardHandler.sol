// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

interface IVaultRewardHandler {
    function sell(uint256 _amount) external;

    function setPendingOwner(address _po) external;

    function applyPendingOwner() external;

    function rescueToken(address _token, address _to) external;
}
