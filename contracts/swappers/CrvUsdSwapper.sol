// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "../../interfaces/ICurveTriCryptoFactoryNG.sol";

contract CrvUsdSwapper is Ownable {
    using SafeERC20 for IERC20;

    address public constant TRICRV_POOL =
        0x4eBdF703948ddCEA3B11f675B4D1Fba9d2414A14;
    address public constant CRVUSD_TOKEN =
        0xf939E0A03FB07F59A73314E73794Be0E57ac1b4E;

    address public depositor;
    bool public useOracle = true;
    uint256 public allowedSlippage = 9700;
    uint256 public constant DECIMALS = 10000;
    uint256 public constant TRICRV_ETH_INDEX = 1;
    uint256 public constant TRICRV_CRVUSD_INDEX = 0;

    ICurveTriCryptoFactoryNG triCrvSwap = ICurveTriCryptoFactoryNG(TRICRV_POOL);

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
    }

    /// @notice Change the contract authorized to call buy and sell functions
    /// @param _depositor - address of the new depositor
    function updateDepositor(address _depositor) external onlyOwner {
        require(_depositor != address(0));
        depositor = _depositor;
    }

    /// @notice Buy PRISMA with ETH
    /// @param amount - amount of ETH to buy with
    /// @return amount of PRISMA bought
    /// @dev ETH must have been sent to the contract prior
    function buy(uint256 amount) external onlyDepositor returns (uint256) {
        return _swapEthCrvUsd(amount, true);
    }

    /// @notice Sell PRISMA for ETH
    /// @param amount - amount of PRISMA to sell
    /// @return amount of ETH bought
    /// @dev PRISMA must have been sent to the contract prior
    function sell(uint256 amount) external onlyDepositor returns (uint256) {
        return _swapEthCrvUsd(amount, false);
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
        return
            triCrvSwap.exchange_underlying{value: ethToCrvUsd ? amount : 0}(
                ethToCrvUsd ? TRICRV_ETH_INDEX : TRICRV_CRVUSD_INDEX,
                ethToCrvUsd ? TRICRV_CRVUSD_INDEX : TRICRV_ETH_INDEX,
                amount,
                _minAmountOut,
                depositor
            );
    }

    /// @notice Wrapper function around TriCrv oracle to return ETH price of crvUSD
    /// @dev This is to work with the Union contract which needs ETH price of asset
    /// @return ETH price of crvUSD
    function price_oracle() external view returns (uint256) {
        return (1e18 * 1e18) / triCrvSwap.price_oracle(0);
    }

    receive() external payable {}

    modifier onlyDepositor() {
        require(msg.sender == depositor, "Depositor only");
        _;
    }
}
