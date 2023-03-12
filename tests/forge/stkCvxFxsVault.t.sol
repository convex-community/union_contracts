// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "forge-std/Test.sol";

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {stkCvxFxsVault} from "contracts/strategies/stkCvxFXS/stkCvxFxsVault.sol";

contract stkCvxFxsVaultTest is Test {
    bytes public constant NOT_OWNER_ERROR =
        bytes("Ownable: caller is not the owner");
    ERC20 private constant CVX_FXS =
        ERC20(0xFEEf77d3f69374f66429C91d732A244f074bdf74);

    stkCvxFxsVault private immutable vault;

    constructor() {
        vault = new stkCvxFxsVault(address(CVX_FXS));
    }

    function testCannotSetHarvestPermissionsNotOwner() external {
        vm.prank(address(0));
        vm.expectRevert(NOT_OWNER_ERROR);

        vault.setHarvestPermissions(false);
    }

    function testSetHarvestPermissions() external {
        assertEq(address(this), vault.owner());
        assertFalse(vault.isHarvestPermissioned());

        vault.setHarvestPermissions(true);

        assertTrue(vault.isHarvestPermissioned());
    }

    function testSetHarvestPermissionsFuzz(bool status) external {
        assertEq(address(this), vault.owner());

        vault.setHarvestPermissions(status);

        assertEq(status, vault.isHarvestPermissioned());
    }

    function testCannotUpdateAuthorizedHarvesters() external {
        vm.prank(address(0));
        vm.expectRevert(NOT_OWNER_ERROR);

        vault.updateAuthorizedHarvesters(address(0), true);
    }

    function testUpdateAuthorizedHarvesters() external {
        assertFalse(vault.authorizedHarvesters(address(0)));
        assertEq(address(this), vault.owner());

        vault.updateAuthorizedHarvesters(address(0), true);
    }

    function testUpdateAuthorizedHarvestersFuzz(
        address _harvester,
        bool _authorized
    ) external {
        assertFalse(vault.authorizedHarvesters(_harvester));
        assertEq(address(this), vault.owner());

        vault.updateAuthorizedHarvesters(_harvester, _authorized);

        assertEq(_authorized, vault.authorizedHarvesters(_harvester));
    }
}
