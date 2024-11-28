// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "./GenericDistributor.sol";
import "../../interfaces/IERC4626.sol";

contract sCrvUsdDistributor is GenericDistributor {
    using SafeERC20 for IERC20;

    uint256 private constant DECIMALS = 1e9;
    uint256 public platformFee = 4e7;
    address public platform = 0x9Bc7c6ad7E7Cf3A6fCB58fb21e27752AC1e53f99;

    event PlatformFeeUpdated(uint256 _fee);
    event PlatformUpdated(address indexed _platform);

    /// @notice Updates the part of incentives redirected to the platform
    /// @param _fee - the amount of the new platform fee (in BIPS)
    function setPlatformFee(uint256 _fee) external onlyAdmin {
        assert(_fee < 1e8);
        platformFee = _fee;
        emit PlatformFeeUpdated(_fee);
    }

    /// @notice Updates the address to which platform fees are paid out
    /// @param _platform - the new platform wallet address
    function setPlatform(
        address _platform
    ) external onlyAdmin notToZeroAddress(_platform) {
        platform = _platform;
        emit PlatformUpdated(_platform);
    }

    constructor(
        address _vault,
        address _depositor,
        address _token
    ) GenericDistributor(_vault, _depositor, _token) {}

    /// @notice Stakes the contract's entire crvUSD balance in the scrvUSD Vault
    function stake() external override onlyAdminOrDistributor {
        uint256 _scrvUsdBalancce = IERC4626(vault).maxDeposit(address(this));
        uint256 _feeAmount = (_scrvUsdBalancce * platformFee) / DECIMALS;
        IERC4626(vault).transfer(platform, _feeAmount);
    }
}
