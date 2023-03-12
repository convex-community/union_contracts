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

    event Harvest(address indexed _caller, uint256 _value);
    event Deposit(address indexed _from, address indexed _to, uint256 _value);
    event Withdraw(address indexed _from, address indexed _to, uint256 _value);

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

    function _calculateShares(
        uint256 amount
    ) private view returns (uint256 shares) {
        if (vault.totalSupply() == 0) {
            shares = amount;
        } else {
            // This method should be called BEFORE the deposit
            shares = (amount * vault.totalSupply()) / vault.totalUnderlying();
        }
    }

    function _deposit(
        address to,
        uint256 amount
    ) private returns (uint256) {
        _mintAssets(to, amount);

        CVX_FXS.approve(address(vault), amount);

        return vault.deposit(to, amount);
    }

    function testCannotSetHarvestPermissionsNotOwner() external {
        bool status = false;

        vm.prank(address(0));
        vm.expectRevert(NOT_OWNER_ERROR);

        vault.setHarvestPermissions(status);
    }

    function testSetHarvestPermissions() external {
        bool status = true;

        assertEq(address(this), vault.owner());
        assertFalse(vault.isHarvestPermissioned());

        vault.setHarvestPermissions(status);

        assertTrue(vault.isHarvestPermissioned());
    }

    function testSetHarvestPermissionsFuzz(bool status) external {
        assertEq(address(this), vault.owner());

        vault.setHarvestPermissions(status);

        assertEq(status, vault.isHarvestPermissioned());
    }

    function testCannotUpdateAuthorizedHarvesters() external {
        address invalidHarvester = address(0);
        bool authorized = true;

        vm.prank(address(0));
        vm.expectRevert(NOT_OWNER_ERROR);

        vault.updateAuthorizedHarvesters(invalidHarvester, authorized);
    }

    function testUpdateAuthorizedHarvesters() external {
        address _harvester = address(this);
        bool authorized = true;

        assertFalse(vault.authorizedHarvesters(_harvester));
        assertEq(address(this), vault.owner());

        vault.updateAuthorizedHarvesters(_harvester, authorized);

        assertTrue(vault.authorizedHarvesters(_harvester));
    }

    function testUpdateAuthorizedHarvestersFuzz(
        address _harvester,
        bool authorized
    ) external {
        assertFalse(vault.authorizedHarvesters(_harvester));
        assertEq(address(this), vault.owner());

        vault.updateAuthorizedHarvesters(_harvester, authorized);

        assertEq(authorized, vault.authorizedHarvesters(_harvester));
    }

    function testCannotDepositZeroAddress() external {
        address invalidTo = address(0);
        uint256 amount = 1e18;

        vm.expectRevert(bytes("Invalid address!"));

        vault.deposit(invalidTo, amount);
    }

    function testCannotDepositZeroAmount() external {
        address to = address(this);
        uint256 invalidAmount = 0;

        vm.expectRevert(bytes("Deposit too small"));

        vault.deposit(to, invalidAmount);
    }

    function testDeposit() external {
        address caller = address(this);
        address to = address(this);
        uint256 amount = 1e18;

        _mintAssets(caller, amount);

        uint256 strategyStkCvxFxsBalanceBeforeDeposit = STK_CVX_FXS.balanceOf(
            address(strategy)
        );
        uint256 callerCvxFxsBalanceBeforeDeposit = CVX_FXS.balanceOf(caller);
        uint256 expectedSharesReceived = _calculateShares(amount);

        CVX_FXS.approve(address(vault), amount);

        vm.expectEmit(true, true, false, true, address(vault));

        emit Deposit(address(this), to, amount);

        uint256 shares = vault.deposit(to, amount);

        assertEq(
            strategyStkCvxFxsBalanceBeforeDeposit + amount,
            STK_CVX_FXS.balanceOf(address(strategy))
        );
        assertEq(
            callerCvxFxsBalanceBeforeDeposit - amount,
            CVX_FXS.balanceOf(caller)
        );
        assertEq(expectedSharesReceived, vault.balanceOf(to));
        assertEq(expectedSharesReceived, shares);
    }

    function testDepositFuzz(address to, uint80 amount) external {
        vm.assume(to != address(0));
        vm.assume(amount != 0);
        vm.assume(amount < 10_000e18);

        address caller = address(this);

        _mintAssets(caller, amount);

        uint256 strategyStkCvxFxsBalanceBeforeDeposit = STK_CVX_FXS.balanceOf(
            address(strategy)
        );
        uint256 callerCvxFxsBalanceBeforeDeposit = CVX_FXS.balanceOf(caller);
        uint256 expectedSharesReceived = _calculateShares(amount);

        CVX_FXS.approve(address(vault), amount);

        vm.expectEmit(true, true, false, true, address(vault));

        emit Deposit(caller, to, amount);

        uint256 shares = vault.deposit(to, amount);

        assertEq(
            strategyStkCvxFxsBalanceBeforeDeposit + amount,
            STK_CVX_FXS.balanceOf(address(strategy))
        );
        assertEq(
            callerCvxFxsBalanceBeforeDeposit - amount,
            CVX_FXS.balanceOf(caller)
        );
        assertEq(expectedSharesReceived, vault.balanceOf(to));
        assertEq(expectedSharesReceived, shares);
    }

    function testCannotWithdrawZeroAddress() external {
        address invalidTo = address(0);
        uint256 amount = 1e18;

        vm.expectRevert(bytes("Invalid address!"));

        vault.withdraw(invalidTo, amount);
    }

    function testWithdraw() external {
        address caller = address(this);
        address to = address(this);
        uint256 amount = 1e18;

        _deposit(caller, amount);

        uint256 strategyStkCvxFxsBalanceBeforeWithdraw = STK_CVX_FXS.balanceOf(
            address(strategy)
        );
        uint256 callerSharesBalanceBeforeWithdraw = vault.balanceOf(caller);
        uint256 receiverCvxFxsBalanceBeforeWithdraw = CVX_FXS.balanceOf(to);

        vm.expectEmit(true, true, false, true, address(vault));

        emit Withdraw(caller, to, amount);

        uint256 withdrawn = vault.withdraw(to, amount);

        // NOTE: Does NOT take into account rewards
        assertEq(
            strategyStkCvxFxsBalanceBeforeWithdraw - amount,
            STK_CVX_FXS.balanceOf(address(strategy))
        );
        assertEq(
            callerSharesBalanceBeforeWithdraw - amount,
            vault.balanceOf(caller)
        );
        assertEq(
            receiverCvxFxsBalanceBeforeWithdraw + amount,
            CVX_FXS.balanceOf(to)
        );
        assertEq(amount, withdrawn);
    }

    function testWithdrawFuzz(address to, uint80 amount) external {
        vm.assume(to != address(0));
        vm.assume(amount != 0);
        vm.assume(amount < 10_000e18);

        address caller = address(this);

        _deposit(caller, amount);

        uint256 strategyStkCvxFxsBalanceBeforeWithdraw = STK_CVX_FXS.balanceOf(
            address(strategy)
        );
        uint256 callerSharesBalanceBeforeWithdraw = vault.balanceOf(caller);
        uint256 receiverCvxFxsBalanceBeforeWithdraw = CVX_FXS.balanceOf(to);

        vm.expectEmit(true, true, false, true, address(vault));

        emit Withdraw(caller, to, amount);

        uint256 withdrawn = vault.withdraw(to, amount);

        // NOTE: Does NOT take into account rewards - consider different methods
        // of introducing entropy to improve testing effectiveness
        assertEq(
            strategyStkCvxFxsBalanceBeforeWithdraw - amount,
            STK_CVX_FXS.balanceOf(address(strategy))
        );
        assertEq(
            callerSharesBalanceBeforeWithdraw - amount,
            vault.balanceOf(caller)
        );
        assertEq(
            receiverCvxFxsBalanceBeforeWithdraw + amount,
            CVX_FXS.balanceOf(to)
        );
        assertEq(amount, withdrawn);
    }

    function testCannotHarvestNotAuthorizedHarvester() external {
        uint256 minAmountOut = 0;

        _deposit(address(this), 1);

        vault.setHarvestPermissions(true);

        assertTrue(vault.isHarvestPermissioned());
        assertFalse(vault.authorizedHarvesters(address(this)));
        assertGt(vault.totalSupply(), 0);

        vm.expectRevert(bytes("permissioned harvest"));

        vault.harvest(minAmountOut);
    }

    function testHarvestNotPermissioned() external {
        address caller = address(this);
        uint256 minAmountOut = 0;

        _deposit(address(this), 1);

        assertFalse(vault.isHarvestPermissioned());
        assertFalse(vault.authorizedHarvesters(caller));
        assertGt(vault.totalSupply(), 0);

        vm.expectEmit(true, false, false, true, address(vault));

        emit Harvest(caller, minAmountOut);

        vault.harvest(minAmountOut);
    }

    function testHarvestAuthorizedHarvester() external {
        address caller = address(this);
        uint256 minAmountOut = 0;

        _deposit(address(this), 1);

        vault.setHarvestPermissions(true);
        vault.updateAuthorizedHarvesters(address(this), true);

        assertTrue(vault.isHarvestPermissioned());
        assertTrue(vault.authorizedHarvesters(caller));
        assertGt(vault.totalSupply(), 0);

        vm.expectEmit(true, false, false, true, address(vault));

        emit Harvest(caller, minAmountOut);

        vault.harvest(minAmountOut);
    }

    function testHarvestTotalSupplyZero() external {
        address caller = address(this);
        uint256 minAmountOut = 0;

        vault.setHarvestPermissions(true);

        assertTrue(vault.isHarvestPermissioned());
        assertFalse(vault.authorizedHarvesters(caller));
        assertEq(vault.totalSupply(), 0);

        vm.expectEmit(true, false, false, true, address(vault));

        emit Harvest(caller, minAmountOut);

        vault.harvest(minAmountOut);
    }
}
