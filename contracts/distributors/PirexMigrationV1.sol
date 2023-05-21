// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "../../interfaces/IGenericVault.sol";
import "../../interfaces/IUnionVault.sol";
import "../../interfaces/IGenericDistributor.sol";

contract PirexMigrationV1 is Ownable {
    using SafeERC20 for IERC20;

    address private constant UCVX_TOKEN =
        0x8659Fc767cad6005de79AF65dAfE4249C57927AF;

    address private constant UNION_CVX_DISTRIBUTOR =
        0x27A11054b62C29c166F3FAb2b0aC708043b0CB49;

    function migrate(
        uint256 index,
        address account,
        uint256 amount,
        bytes32[] calldata merkleProof,
        address newDistributor
    ) external onlyOwner {
        IGenericDistributor(UNION_CVX_DISTRIBUTOR).claim(
            index,
            account,
            amount,
            merkleProof
        );
        IERC20(UCVX_TOKEN).safeTransfer(newDistributor, amount);
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
