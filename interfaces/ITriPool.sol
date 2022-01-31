// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

interface ITriPool {
    function add_liquidity(uint256[3] calldata amounts, uint256 min_mint_amount)
        external;

    function get_virtual_price() external view returns (uint256);
}
