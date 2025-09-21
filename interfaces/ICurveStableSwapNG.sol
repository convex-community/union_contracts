// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

interface ICurveStableSwapNG {
    function exchange(
        int128 i,
        int128 j,
        uint256 dx,
        uint256 min_dy,
        address receiver
    ) external returns (uint256);

    function get_dy(
        int128 i,
        int128 j,
        uint256 dx
    ) external view returns (uint256);

    function price_oracle(uint256 k) external view returns (uint256);

    function get_virtual_price() external view returns (uint256);
}