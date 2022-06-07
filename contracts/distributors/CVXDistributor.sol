// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "./GenericDistributor.sol";
import "../../interfaces/IPirexCVX.sol";

contract CVXMerkleDistributor is GenericDistributor {
    constructor(
        address _pirexCVX,
        address _depositor,
        address _token
    ) GenericDistributor(_pirexCVX, _depositor, _token) {}

    /// @notice Stakes the contract's entire CVX balance in the Vault
    function stake() external override onlyAdminOrDistributor {
        IPirexCVX(vault).deposit(
            IERC20(token).balanceOf(address(this)),
            address(this),
            true,
            address(0)
        );
    }
}
