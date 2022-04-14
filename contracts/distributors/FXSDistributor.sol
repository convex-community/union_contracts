// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "./GenericDistributor.sol";

interface IVaultZaps {
    function depositFromUnderlyingAssets(
        uint256[2] calldata amounts,
        uint256 minAmountOut,
        address to
    ) external;
}

contract FXSMerkleDistributorV2 is GenericDistributor {
    using SafeERC20 for IERC20;

    address public vaultZap;

    address public constant FXS_TOKEN =
        0x3432B6A60D23Ca0dFCa7761B7ab56459D9C964D0;

    // This event is triggered whenever the zap contract is updated.
    event ZapUpdated(address indexed oldZap, address indexed newZap);

    constructor(
        address _vault,
        address _depositor,
        address _zap
    ) GenericDistributor(_vault, _depositor, FXS_TOKEN) {
        require(_zap != address(0));
        vaultZap = _zap;
    }

    /// @notice Changes the Zap for deposits
    /// @param newZap - address of the new zap
    function updateZap(address newZap)
        external
        onlyAdmin
        notToZeroAddress(newZap)
    {
        address oldZap = vaultZap;
        vaultZap = newZap;
        emit ZapUpdated(oldZap, vaultZap);
    }

    /// @notice Set approvals for the tokens used when swapping
    function setApprovals() external override onlyAdmin {
        IERC20(token).safeApprove(vaultZap, 0);
        IERC20(token).safeApprove(vaultZap, type(uint256).max);
    }

    /// @notice Stakes the contract's entire cvxCRV balance in the Vault
    function stake() external override onlyAdminOrDistributor {
        IVaultZaps(vaultZap).depositFromUnderlyingAssets(
            [IERC20(FXS_TOKEN).balanceOf(address(this)), 0],
            0,
            address(this)
        );
    }
}
