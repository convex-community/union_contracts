// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

interface IAuraMining {
    function ConvertBalToAura(uint256 _amount, uint256 minterMinted)
        external
        view
        returns (uint256);
}
