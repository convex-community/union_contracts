// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "forge-std/Test.sol";

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {stkCvxFxsVault} from "contracts/strategies/stkCvxFXS/stkCvxFxsVault.sol";

contract stkCvxFxsVaultTest is Test {
    ERC20 private constant CVX_FXS =
        ERC20(0xFEEf77d3f69374f66429C91d732A244f074bdf74);
    stkCvxFxsVault private immutable vault;

    constructor() {
        vault = new stkCvxFxsVault(address(CVX_FXS));
    }

    function testCannotSetHarvestPermissionsNotOwner() external {
        vm.prank(address(0));
        vm.expectRevert(bytes("Ownable: caller is not the owner"));

        vault.setHarvestPermissions(false);
    }

    function testSetHarvestPermissions() external {
        assertEq(address(this), vault.owner());
        assertFalse(vault.isHarvestPermissioned());

        vault.setHarvestPermissions(true);

        assertTrue(vault.isHarvestPermissioned());
    }
}
