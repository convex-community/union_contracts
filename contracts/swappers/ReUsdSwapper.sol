// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "../../interfaces/ICurveTriCryptoFactoryNG.sol";
import "../../interfaces/IERC4626.sol";
import "../../interfaces/ICurveStableSwapNG.sol";

contract ReUsdSwapper is Ownable {
    using SafeERC20 for IERC20;

    address public constant TRICRV_POOL =
        0x4eBdF703948ddCEA3B11f675B4D1Fba9d2414A14;
    address public constant CRVUSD_TOKEN =
        0xf939E0A03FB07F59A73314E73794Be0E57ac1b4E;
    address public constant REUSD_TOKEN =
        0x57aB1E0003F623289CD798B1824Be09a793e4Bec;
    // scrvUSD vault for wrapping crvUSD
    address public constant SCRVUSD_VAULT =
        0x0655977FEb2f289A4aB78af67BAB0d17aAb84367;
    // Curve StableSwapNG pool for scrvUSD <-> reUSD
    address public constant REUSD_POOL =
        0xc522A6606BBA746d7960404F22a3DB936B6F4F50;
    // scrvUSD token (from vault)
    address public constant SCRVUSD_TOKEN = SCRVUSD_VAULT;

    address public depositor;
    bool public useOracle = true;
    uint256 public allowedSlippage = 9700;
    uint256 public constant DECIMALS = 10000;
    uint256 public constant TRICRV_ETH_INDEX = 1;
    uint256 public constant TRICRV_CRVUSD_INDEX = 0;
    // Pool indices: reUSD = 0, scrvUSD = 1
    int128 private constant REUSD_INDEX = 0;
    int128 private constant SCRVUSD_INDEX = 1;

    ICurveTriCryptoFactoryNG triCrvSwap = ICurveTriCryptoFactoryNG(TRICRV_POOL);
    IERC4626 private immutable scrvUsdVault = IERC4626(SCRVUSD_VAULT);
    ICurveStableSwapNG private immutable reUsdPool =
        ICurveStableSwapNG(REUSD_POOL);

    constructor(address _depositor) {
        require(_depositor != address(0));
        depositor = _depositor;
    }

    /// @notice Turns oracle on or off for swap
    function switchOracle() external onlyOwner {
        useOracle = !useOracle;
    }

    /// @notice Set approvals for the contracts used when swapping & staking
    function setApprovals() external {
        IERC20(CRVUSD_TOKEN).safeApprove(TRICRV_POOL, 0);
        IERC20(CRVUSD_TOKEN).safeApprove(TRICRV_POOL, type(uint256).max);

        // Set approval for scrvUSD vault (for crvUSD wrapping)
        IERC20(CRVUSD_TOKEN).safeApprove(SCRVUSD_VAULT, 0);
        IERC20(CRVUSD_TOKEN).safeApprove(SCRVUSD_VAULT, type(uint256).max);

        // Set approval for reUSD pool (for scrvUSD -> reUSD swap)
        IERC20(SCRVUSD_TOKEN).safeApprove(REUSD_POOL, 0);
        IERC20(SCRVUSD_TOKEN).safeApprove(REUSD_POOL, type(uint256).max);

        // Set approval for reUSD token (for reUSD -> scrvUSD swap)
        IERC20(REUSD_TOKEN).safeApprove(REUSD_POOL, 0);
        IERC20(REUSD_TOKEN).safeApprove(REUSD_POOL, type(uint256).max);
    }

    /// @notice Change the contract authorized to call buy and sell functions
    /// @param _depositor - address of the new depositor
    function updateDepositor(address _depositor) external onlyOwner {
        require(_depositor != address(0));
        depositor = _depositor;
    }

    /// @notice Buy reUSD with ETH
    /// @param amount - amount of ETH to buy with
    /// @return amount of reUSD bought
    /// @dev ETH must have been sent to the contract prior
    function buy(uint256 amount) external onlyDepositor returns (uint256) {
        // Step 1: ETH -> crvUSD
        uint256 crvUsdAmount = _swapEthCrvUsd(amount, true);

        // Step 2: crvUSD -> scrvUSD -> reUSD
        return _swapCrvUsdToReUsd(crvUsdAmount);
    }

    /// @notice Sell reUSD for ETH
    /// @param amount - amount of reUSD to sell
    /// @return amount of ETH bought
    /// @dev reUSD must have been sent to the contract prior
    function sell(uint256 amount) external onlyDepositor returns (uint256) {
        // Step 1: reUSD -> scrvUSD -> crvUSD
        uint256 crvUsdAmount = _swapReUsdToCrvUsd(amount);

        // Step 2: crvUSD -> ETH
        return _swapEthCrvUsd(crvUsdAmount, false);
    }

    /// @notice Swap ETH<->crvUSD on Curve via triCRV pool
    /// @param amount - amount to swap
    /// @param ethToCrvUsd - whether to swap from eth to prisma or the inverse
    /// @return amount of token obtained after the swap
    function _swapEthCrvUsd(
        uint256 amount,
        bool ethToCrvUsd
    ) internal returns (uint256) {
        uint256 _minAmountOut = 0;
        if (useOracle) {
            uint256 _ethCrvUsdPrice = triCrvSwap.price_oracle(0);
            uint256 _oracleAmount = ethToCrvUsd
                ? (amount * _ethCrvUsdPrice) / 1e18
                : (amount * 1e18) / _ethCrvUsdPrice;
            _minAmountOut = ((_oracleAmount * allowedSlippage) / DECIMALS);
        }
        // Receiver logic:
        // - On ETH -> crvUSD, send crvUSD to this contract so it can wrap/deposit next.
        // - On crvUSD -> ETH, send ETH to the depositor (zap) directly.
        address _receiver = ethToCrvUsd ? address(this) : depositor;

        return
            triCrvSwap.exchange_underlying{value: ethToCrvUsd ? amount : 0}(
                ethToCrvUsd ? TRICRV_ETH_INDEX : TRICRV_CRVUSD_INDEX,
                ethToCrvUsd ? TRICRV_CRVUSD_INDEX : TRICRV_ETH_INDEX,
                amount,
                _minAmountOut,
                _receiver
            );
    }

    /// @notice Internal function to swap crvUSD -> scrvUSD -> reUSD
    /// @param crvUsdAmount Amount of crvUSD to swap
    /// @return Amount of reUSD received
    function _swapCrvUsdToReUsd(
        uint256 crvUsdAmount
    ) internal returns (uint256) {
        // Step 1: Wrap crvUSD to scrvUSD via ERC4626 vault (no slippage here)
        uint256 scrvUsdAmount = scrvUsdVault.deposit(
            crvUsdAmount,
            address(this)
        );

        // Step 2: Swap scrvUSD to reUSD via Curve pool with slippage protection
        uint256 minReUsdOut = 0;
        if (useOracle) {
            // Get expected reUSD amount using oracle price
            uint256 oraclePrice = reUsdPool.price_oracle(0); // reUSD/scrvUSD price
            uint256 expectedReUsd = (scrvUsdAmount * 1e18) / oraclePrice;
            minReUsdOut = (expectedReUsd * allowedSlippage) / DECIMALS;
        }

        return
            reUsdPool.exchange(
                SCRVUSD_INDEX,
                REUSD_INDEX,
                scrvUsdAmount,
                minReUsdOut,
                depositor
            );
    }

    /// @notice Internal function to swap reUSD -> scrvUSD -> crvUSD
    /// @param reUsdAmount Amount of reUSD to swap
    /// @return Amount of crvUSD received
    function _swapReUsdToCrvUsd(
        uint256 reUsdAmount
    ) internal returns (uint256) {
        // Step 1: Swap reUSD to scrvUSD via Curve pool with slippage protection
        uint256 minScrvUsdOut = 0;
        if (useOracle) {
            // Get expected scrvUSD amount using oracle price
            uint256 oraclePrice = reUsdPool.price_oracle(0); // reUSD/scrvUSD price
            uint256 expectedScrvUsd = (reUsdAmount * oraclePrice) / 1e18;
            minScrvUsdOut = (expectedScrvUsd * allowedSlippage) / DECIMALS;
        }

        uint256 scrvUsdAmount = reUsdPool.exchange(
            REUSD_INDEX,
            SCRVUSD_INDEX,
            reUsdAmount,
            minScrvUsdOut,
            address(this)
        );

        // Step 2: Unwrap scrvUSD to crvUSD via ERC4626 vault (no slippage here)
        return scrvUsdVault.redeem(scrvUsdAmount, address(this), address(this));
    }

    /// @notice Wrapper function around pricing oracles to return ETH price of reUSD
    /// @dev Combines TriCrv oracle, scrvUSD vault pricePerShare, and Curve pool oracle
    /// @return ETH price of reUSD
    function price_oracle() external view returns (uint256) {
        // Get ETH price of crvUSD from TriCrv pool
        uint256 ethPriceOfCrvUsd = (1e18 * 1e18) / triCrvSwap.price_oracle(0);

        // Get crvUSD price of scrvUSD from vault pricePerShare
        uint256 crvUsdPriceOfScrvUsd = scrvUsdVault.convertToAssets(1e18);

        // Get scrvUSD price of reUSD from Curve pool oracle (index 0 = reUSD/scrvUSD)
        uint256 scrvUsdPriceOfReUsd = reUsdPool.price_oracle(0);

        // Chain the prices: ETH -> crvUSD -> scrvUSD -> reUSD
        return
            (ethPriceOfCrvUsd * crvUsdPriceOfScrvUsd * scrvUsdPriceOfReUsd) /
            (1e18 * 1e18);
    }

    receive() external payable {}

    modifier onlyDepositor() {
        require(msg.sender == depositor, "Depositor only");
        _;
    }
}
