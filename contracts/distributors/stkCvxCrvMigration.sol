// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "../../interfaces/IGenericVault.sol";
import "../../interfaces/IUnionVault.sol";
import "../../interfaces/IGenericDistributor.sol";


contract stkCvxCrvMigration is Ownable {
    using SafeERC20 for IERC20;

    address private constant UNION_CRV =
        0x83507cc8C8B67Ed48BADD1F59F684D5d02884C81;

    address private constant UNION_CRV_DISTRIBUTOR =
        0xA83043Df401346A67eddEb074679B4570b956183;

    address private constant CVXCRV_TOKEN =
        0x62B9c7356A2Dc64a1969e19C23e4f579F9810Aa7;

    function migrate(
        uint256 index,
        address account,
        uint256 amount,
        bytes32[] calldata merkleProof,
        address vault,
        address newDistributor
    ) external onlyOwner {
        IGenericDistributor(UNION_CRV_DISTRIBUTOR).claim(
            index,
            account,
            amount,
            merkleProof
        );
        IUnionVault(UNION_CRV).withdrawAll(address(this));
        IERC20(CVXCRV_TOKEN).safeApprove(vault, 0);
        IERC20(CVXCRV_TOKEN).safeApprove(vault, type(uint256).max);
        IGenericVault(vault).depositAll(newDistributor);
    }

    /// @notice Execute calls on behalf of contract in case of emergency
    function execute(
        address _to,
        uint256 _value,
        bytes calldata _data
    ) external onlyOwner returns (bool, bytes memory) {
        (bool success, bytes memory result) = _to.call{value: _value}(_data);
        return (success, result);
    }

    receive() external payable {}
}
