// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "forge-std/Test.sol";

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {stkCvxFxsVault} from "contracts/strategies/stkCvxFXS/stkCvxFxsVault.sol";
import {stkCvxFxsStrategy} from "contracts/strategies/stkCvxFXS/Strategy.sol";
import {stkCvxFxsHarvester} from "contracts/strategies/stkCvxFXS/harvester/Harvester.sol";

interface ICvxFxs {
    function mint(address _receiver, uint256 _amount) external;
}

contract stkCvxFxsVaultTest is Test {
    bytes public constant NOT_OWNER_ERROR =
        bytes("Ownable: caller is not the owner");
    ERC20 private constant CVX_FXS =
        ERC20(0xFEEf77d3f69374f66429C91d732A244f074bdf74);
    ERC20 private constant STK_CVX_FXS =
        ERC20(0x49b4d1dF40442f0C31b1BbAEA3EDE7c38e37E31a);

    stkCvxFxsVault private immutable vault;
    stkCvxFxsStrategy private immutable strategy;
    stkCvxFxsHarvester private immutable harvester;

    constructor() {
        vault = new stkCvxFxsVault(address(CVX_FXS));
        strategy = new stkCvxFxsStrategy(address(vault));
        harvester = new stkCvxFxsHarvester(address(strategy));

        // Configure vault
        vault.setPlatform(address(this));
        vault.setStrategy(address(strategy));

        // Configure strategy
        strategy.setApprovals();
        strategy.setHarvester(address(harvester));

        // Configure harvester
        harvester.setApprovals();
    }

    function _mintAssets(address receiver, uint256 amount) private {
        uint256 balanceBefore = CVX_FXS.balanceOf(receiver);

        // cvxFXS operator (has permission to mint)
        vm.prank(0x8f55d7c21bDFf1A51AFAa60f3De7590222A3181e);

        ICvxFxs(address(CVX_FXS)).mint(address(this), amount);

        vm.prank(receiver);

        assertEq(balanceBefore + amount, CVX_FXS.balanceOf(receiver));
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
