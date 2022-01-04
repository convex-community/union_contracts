// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

interface ICvxMining {
    function ConvertCrvToCvx(uint256 _amount) external view returns (uint256);
}
