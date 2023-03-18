// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "../../interfaces/IGenericVault.sol";

interface IFxsDistributorZaps {
    function claimFromDistributorAsUnderlying(
        uint256 index,
        address account,
        uint256 amount,
        bytes32[] calldata merkleProof,
        uint256 assetIndex,
        uint256 minAmountOut,
        address to
    ) external returns (uint256);
}

contract stkCvxFxsMigration is Ownable {
    using SafeERC20 for IERC20;

    address private constant UNION_FXS_DISTRIBUTOR_ZAPS =
        0x56e9Db574c8D5015d198671cbf1200B6Bb2Ed944;

    address private constant CVXFXS_TOKEN =
        0xFEEf77d3f69374f66429C91d732A244f074bdf74;

    address private constant UNION_FXS =
        0xF964b0E3FfdeA659c44a5a52bc0B82A24b89CE0E;

    /// @notice Claim from the old distributor to cvxFXS and stake on behalf of new distributor
    /// @param vault - address of the new stkCvxFxs vault
    /// @param newDistributor - address of the new stkCvxFxsDistributor
    /// @param minAmountOut - min amount of cvxFXS expected
    function migrate(
        uint256 index,
        address account,
        uint256 amount,
        bytes32[] calldata merkleProof,
        address vault,
        address newDistributor,
        uint256 minAmountOut
    ) external onlyOwner {
        IERC20(UNION_FXS).safeApprove(vault, 0);
        IERC20(UNION_FXS).safeApprove(
            UNION_FXS_DISTRIBUTOR_ZAPS,
            type(uint256).max
        );
        IFxsDistributorZaps(UNION_FXS_DISTRIBUTOR_ZAPS)
            .claimFromDistributorAsUnderlying(
                index,
                account,
                amount,
                merkleProof,
                1,
                minAmountOut,
                address(this)
            );
        IERC20(CVXFXS_TOKEN).safeApprove(vault, 0);
        IERC20(CVXFXS_TOKEN).safeApprove(vault, type(uint256).max);
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
