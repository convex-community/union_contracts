// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "@openzeppelin/contracts/access/Ownable.sol";
import "../../interfaces/IGenericVault.sol";
import "../../interfaces/IGenericDistributor.sol";

contract stkCvxCrvMigration is Ownable {

    function migrate(
        uint256 index,
        address account,
        uint256 amount,
        bytes32[] calldata merkleProof,
        address vault,
        address oldDistributor,
        address newDistributor) external onlyOwner {
        IGenericDistributor(oldDistributor).claim(index, account, amount, merkleProof);
        IGenericVault(vault).approve(newDistributor, 2 ** 256 - 1);
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
