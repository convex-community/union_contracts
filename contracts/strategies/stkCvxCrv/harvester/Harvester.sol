// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "../../../../interfaces/IVaultRewardHandler.sol";
import "../../../../interfaces/ICurvePool.sol";
import "../../../../interfaces/ICurveTriCrypto.sol";
import "../../../../interfaces/ICurveTriCryptoFactoryNG.sol";
import "../../../../interfaces/ICurveV2Pool.sol";
import "../../../../interfaces/ICvxCrvDeposit.sol";
import "../../../../interfaces/ICurveNewFactoryPool.sol";

contract stkCvxCrvHarvester {
    using SafeERC20 for IERC20;
    address public owner;
    address public immutable strategy;
    uint256 public allowedSlippage = 9700;
    uint256 public constant DECIMALS = 10000;
    address public pendingOwner;

    bool public useOracle = true;
    bool public forceLock;

    address private constant CRVUSD_TOKEN =
        0xf939E0A03FB07F59A73314E73794Be0E57ac1b4E;
    address public constant CVX_TOKEN =
        0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B;
    address public constant CRV_TOKEN =
        0xD533a949740bb3306d119CC777fa900bA034cd52;
    address public constant CVXCRV_TOKEN =
        0x62B9c7356A2Dc64a1969e19C23e4f579F9810Aa7;
    address public constant CURVE_CVX_ETH_POOL =
        0xB576491F1E6e5E62f1d8F26062Ee822B40B0E0d4;
    address public constant CURVE_CVXCRV_CRV_POOL =
        0x971add32Ea87f10bD192671630be3BE8A11b8623;
    address private constant CURVE_TRICRV_POOL =
        0x4eBdF703948ddCEA3B11f675B4D1Fba9d2414A14;
    address private constant CVXCRV_DEPOSIT =
        0x8014595F2AB54cD7c604B00E9fb932176fDc86Ae;

    ICurveV2Pool cvxEthSwap = ICurveV2Pool(CURVE_CVX_ETH_POOL);
    ICurveTriCryptoFactoryNG triCrv =
        ICurveTriCryptoFactoryNG(CURVE_TRICRV_POOL);
    ICurveNewFactoryPool crvCvxCrvSwap =
        ICurveNewFactoryPool(CURVE_CVXCRV_CRV_POOL);

    constructor(address _strategy) {
        strategy = _strategy;
        owner = msg.sender;
    }

    /// @notice Set approvals for the contracts used when swapping & staking
    function setApprovals() external {
        IERC20(CRVUSD_TOKEN).safeApprove(CURVE_TRICRV_POOL, 0);
        IERC20(CRVUSD_TOKEN).safeApprove(CURVE_TRICRV_POOL, type(uint256).max);

        IERC20(CVX_TOKEN).safeApprove(CURVE_CVX_ETH_POOL, 0);
        IERC20(CVX_TOKEN).safeApprove(CURVE_CVX_ETH_POOL, type(uint256).max);

        IERC20(CRV_TOKEN).safeApprove(CVXCRV_DEPOSIT, 0);
        IERC20(CRV_TOKEN).safeApprove(CVXCRV_DEPOSIT, type(uint256).max);

        IERC20(CRV_TOKEN).safeApprove(CURVE_CVXCRV_CRV_POOL, 0);
        IERC20(CRV_TOKEN).safeApprove(CURVE_CVXCRV_CRV_POOL, type(uint256).max);
    }

    /// @notice Turns oracle on or off for swap
    function switchOracle() external onlyOwner {
        useOracle = !useOracle;
    }

    function setPendingOwner(address _po) external onlyOwner {
        pendingOwner = _po;
    }

    function acceptOwnership() external {
        require(pendingOwner == msg.sender, "only new owner");
        owner = pendingOwner;
        pendingOwner = address(0);
    }

    /// @notice switch the forceLock option to force harvester to lock
    /// @dev the harvester will lock even if there is a discount if forceLock is true
    function setForceLock() external onlyOwner {
        forceLock = !forceLock;
    }

    /// @notice Rescue tokens wrongly sent to the contracts or claimed extra
    /// rewards that the contract is not equipped to handle
    /// @dev Unhandled rewards can be redirected to new harvester contract
    function rescueToken(address _token, address _to) external onlyOwner {
        /// Only allow to rescue non-supported tokens
        require(
            _token != CRV_TOKEN &&
                _token != CVX_TOKEN &&
                _token != CRVUSD_TOKEN,
            "not allowed"
        );
        uint256 _balance = IERC20(_token).balanceOf(address(this));
        IERC20(_token).safeTransfer(_to, _balance);
    }

    function setSlippage(uint256 _slippage) external onlyOwner {
        allowedSlippage = _slippage;
    }

    /// @notice Compute a min amount of ETH based on pool oracle for cvx
    /// @param _amount - amount to swap
    /// @return min acceptable amount of ETH
    function _calcMinAmountOutCvxEth(
        uint256 _amount
    ) internal returns (uint256) {
        uint256 _cvxEthPrice = cvxEthSwap.price_oracle();
        uint256 _amountEthPrice = (_amount * _cvxEthPrice) / 1e18;
        return ((_amountEthPrice * allowedSlippage) / DECIMALS);
    }

    function _cvxToEth(uint256 _amount) internal {
        uint256 _minAmountOut = useOracle
            ? _calcMinAmountOutCvxEth(_amount)
            : 0;
        cvxEthSwap.exchange_underlying{value: 0}(1, 0, _amount, _minAmountOut);
    }

    /// @notice Compute a min amount of CRV based on pool oracle for crvUSD
    /// @param _amount - amount to swap
    /// @return min acceptable amount of ETH
    function _calcMinAmountOutCrvUsdCrv(
        uint256 _amount
    ) internal returns (uint256) {
        /// get CRV price in crvUSD from triCrv pool
        uint256 _crvPriceInCrvUsd = triCrv.price_oracle(1);
        uint256 _amountCrv = ((_amount * 1e18) / _crvPriceInCrvUsd);
        return ((_amountCrv * allowedSlippage) / DECIMALS);
    }

    function _crvUsdToCrv(uint256 _amount) internal {
        uint256 _minAmountOut = useOracle
            ? _calcMinAmountOutCrvUsdCrv(_amount)
            : 0;
        if (_amount > 0) {
            triCrv.exchange(0, 2, _amount, _minAmountOut, false);
        }
    }

    /// @notice Compute a min amount of CRV based on pool oracle for ETH
    /// @param _amount - amount to swap
    /// @return min acceptable amount of CRV
    function _calcMinAmountOutEthCrv(
        uint256 _amount
    ) internal returns (uint256) {
        uint256 _amountCrvPrice = ((_amount * triCrv.price_oracle(0)) /
            triCrv.price_oracle(1));
        return ((_amountCrvPrice * allowedSlippage) / DECIMALS);
    }

    function _ethToCrv(uint256 _amount) internal {
        if (_amount > 0) {
            uint256 _minAmountOut = useOracle
                ? _calcMinAmountOutEthCrv(_amount)
                : 0;
            triCrv.exchange{value: _amount}(1, 2, _amount, _minAmountOut, true);
        }
    }

    function _crvToCvxCrv(
        uint256 _amount,
        uint256 _minAmounOut
    ) internal returns (uint256) {
        return
            crvCvxCrvSwap.exchange(0, 1, _amount, _minAmounOut, address(this));
    }

    function processRewards() external onlyStrategy returns (uint256) {
        uint256 _cvxBalance = IERC20(CVX_TOKEN).balanceOf(address(this));
        if (_cvxBalance > 0) {
            _cvxToEth(_cvxBalance);
            _ethToCrv(address(this).balance);
        }
        uint256 _crvUsdBalance = IERC20(CRVUSD_TOKEN).balanceOf(address(this));
        if (_crvUsdBalance > 0) {
            _crvUsdToCrv(_crvUsdBalance);
        }
        uint256 _crvBalance = IERC20(CRV_TOKEN).balanceOf(address(this));
        if (_crvBalance > 0) {
            // use the pool's price oracle to determine if there's a swap discount
            uint256 _priceOracle = crvCvxCrvSwap.price_oracle();
            // swap on Curve if there is a discount for doing so
            // and if we are not set to lock
            if ((_priceOracle < 1 ether) && !forceLock) {
                // we compute a minamountout using the price oracle
                _crvToCvxCrv(
                    _crvBalance,
                    (((_crvBalance / _priceOracle) * 1e18) * allowedSlippage) /
                        DECIMALS
                );
            }
            // otherwise lock
            else {
                ICvxCrvDeposit(CVXCRV_DEPOSIT).deposit(_crvBalance, true);
            }
            uint256 _cvxCrvBalance = IERC20(CVXCRV_TOKEN).balanceOf(
                address(this)
            );
            IERC20(CVXCRV_TOKEN).safeTransfer(msg.sender, _cvxCrvBalance);
            return _cvxCrvBalance;
        }
        return 0;
    }

    modifier onlyOwner() {
        require((msg.sender == owner), "owner only");
        _;
    }

    modifier onlyStrategy() {
        require((msg.sender == strategy), "strategy only");
        _;
    }

    receive() external payable {}
}
