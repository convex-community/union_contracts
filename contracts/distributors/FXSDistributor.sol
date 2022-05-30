// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "./GenericDistributor.sol";
import "../../interfaces/ICurveV2Pool.sol";

interface IVaultZaps {
    function depositFromUnderlyingAssets(
        uint256[2] calldata amounts,
        uint256 minAmountOut,
        address to
    ) external;
}

contract FXSMerkleDistributor is GenericDistributor {
    using SafeERC20 for IERC20;

    address public vaultZap;

    address private constant FXS_TOKEN =
        0x3432B6A60D23Ca0dFCa7761B7ab56459D9C964D0;

    address private constant CURVE_CVXFXS_FXS_POOL =
        0xd658A338613198204DCa1143Ac3F01A722b5d94A;
    address private constant CURVE_FXS_ETH_POOL =
        0x941Eb6F616114e4Ecaa85377945EA306002612FE;

    // 2.5% slippage tolerance by default
    uint256 public slippage = 9750;
    uint256 private constant DECIMALS = 10000;

    ICurveV2Pool private cvxFxsPool = ICurveV2Pool(CURVE_CVXFXS_FXS_POOL);
    ICurveV2Pool private ethFxsPool = ICurveV2Pool(CURVE_FXS_ETH_POOL);

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

    /// @notice Set the acceptable level of slippage for LP deposits
    /// @dev As percentage of the ETH value of original amount in BIPS
    /// @param _slippage - the acceptable slippage threshold
    function setSlippage(uint256 _slippage) external onlyAdmin {
        slippage = _slippage;
    }

    /// @notice Calculates the minimum amount of LP tokens we want to receive
    /// @dev Uses Curve's estimation of received LP tokens & price oracles
    /// @param _amount - the amount of FXS tokens to deposit
    /// @return a min amount we can use to guarantee < x% slippage
    function _calcLPMinAmountOut(uint256 _amount) internal returns (uint256) {
        uint256 _receivedLPTokens = (cvxFxsPool.calc_token_amount(
            [_amount, 0]
        ) * 9900) / DECIMALS;
        uint256 _lpTokenFxsPrice = (_receivedLPTokens * cvxFxsPool.lp_price()) /
            1e18;
        uint256 _fxsEthPrice = ethFxsPool.price_oracle();
        uint256 _lpTokenEthPrice = (_lpTokenFxsPrice * _fxsEthPrice) / 1e18;
        uint256 _amountEthPrice = (_amount * _fxsEthPrice) / 1e18;
        // ensure we're not getting more than x% slippage on ETH value
        require(
            _lpTokenEthPrice > ((_amountEthPrice * slippage) / DECIMALS),
            "slippage"
        );
        return _receivedLPTokens;
    }

    /// @notice Stakes the contract's entire cvxCRV balance in the Vault
    function stake() external override onlyAdminOrDistributor {
        uint256 _balance = IERC20(FXS_TOKEN).balanceOf(address(this));
        IVaultZaps(vaultZap).depositFromUnderlyingAssets(
            [_balance, 0],
            _calcLPMinAmountOut(_balance),
            address(this)
        );
    }
}
