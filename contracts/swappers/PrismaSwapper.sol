// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "../../interfaces/ICurveV2Pool.sol";

contract PrismaSwapper is Ownable {
    using SafeERC20 for IERC20;

    address public constant CURVE_PRISMA_ETH_POOL =
        0x322135Dd9cBAE8Afa84727d9aE1434b5B3EBA44B;
    address public constant PRISMA_TOKEN =
        0xdA47862a83dac0c112BA89c6abC2159b95afd71C;

    address public depositor;
    bool public useOracle = true;
    uint256 public allowedSlippage = 9700;
    uint256 public constant DECIMALS = 10000;
    uint256 public constant PRISMAETH_ETH_INDEX = 0;
    uint256 public constant PRISMAETH_PRISMA_INDEX = 1;

    ICurveV2Pool prismaEthSwap = ICurveV2Pool(CURVE_PRISMA_ETH_POOL);

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
        IERC20(PRISMA_TOKEN).safeApprove(CURVE_PRISMA_ETH_POOL, 0);
        IERC20(PRISMA_TOKEN).safeApprove(
            CURVE_PRISMA_ETH_POOL,
            type(uint256).max
        );
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
        uint256 _received = _swapEthPrisma(amount, true);
        IERC20(PRISMA_TOKEN).safeTransfer(depositor, _received);
        return _received;
    }

    /// @notice Sell PRISMA for ETH
    /// @param amount - amount of PRISMA to sell
    /// @return amount of ETH bought
    /// @dev PRISMA must have been sent to the contract prior
    function sell(uint256 amount) external onlyDepositor returns (uint256) {
        uint256 _received = _swapEthPrisma(amount, false);
        (bool success, ) = depositor.call{value: _received}("");
        require(success, "ETH transfer failed");
        return _received;
    }

    /// @notice Swap ETH<->Prisma on Curve
    /// @param amount - amount to swap
    /// @param ethToPrisma - whether to swap from eth to prisma or the inverse
    /// @return amount of token obtained after the swap
    function _swapEthPrisma(
        uint256 amount,
        bool ethToPrisma
    ) internal returns (uint256) {
        uint256 _minAmountOut = 0;
        if (useOracle) {
            uint256 _ethPrismaPrice = prismaEthSwap.price_oracle();
            uint256 _oracleAmount = ethToPrisma
                ? (amount * 1e18) / _ethPrismaPrice
                : (amount * _ethPrismaPrice) / 1e18;
            _minAmountOut = ((_oracleAmount * allowedSlippage) / DECIMALS);
        }
        return
            prismaEthSwap.exchange_underlying{value: ethToPrisma ? amount : 0}(
                ethToPrisma ? PRISMAETH_ETH_INDEX : PRISMAETH_PRISMA_INDEX,
                ethToPrisma ? PRISMAETH_PRISMA_INDEX : PRISMAETH_ETH_INDEX,
                amount,
                _minAmountOut
            );
    }

    receive() external payable {}

    modifier onlyDepositor() {
        require(msg.sender == depositor, "Depositor only");
        _;
    }
}
