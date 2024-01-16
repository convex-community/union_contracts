// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "./StrategyBase.sol";
import "../../../interfaces/IGenericVault.sol";
import "../../../interfaces/IUniV2Router.sol";
import "../../../interfaces/ICurveTriCrypto.sol";
import "../../../interfaces/ICVXLocker.sol";

contract stkCvxPrismaZaps is Ownable, stkCvxPrismaStrategyBase {
    using SafeERC20 for IERC20;

    address public immutable vault;

    address private constant CONVEX_LOCKER =
        0x72a19342e8F1838460eBFCCEf09F6585e32db86E;
    address private constant TRICRYPTO =
        0xD51a44d3FaE010294C616388b506AcdA1bfAAE46;
    address public constant WETH_TOKEN =
        0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    address public constant USDT_TOKEN =
        0xdAC17F958D2ee523a2206206994597C13D831ec7;
    address public constant UNISWAP_ROUTER =
        0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    ICurveTriCrypto triCryptoSwap = ICurveTriCrypto(TRICRYPTO);
    ICVXLocker locker = ICVXLocker(CONVEX_LOCKER);

    constructor(address _vault) {
        vault = _vault;
    }

    /// @notice Set approvals for the contracts used when swapping & staking
    function setApprovals() external {
        IERC20(CVX_TOKEN).safeApprove(CURVE_CVX_ETH_POOL, 0);
        IERC20(CVX_TOKEN).safeApprove(CURVE_CVX_ETH_POOL, type(uint256).max);

        IERC20(PRISMA_TOKEN).safeApprove(CURVE_CVXPRISMA_PRISMA_POOL, 0);
        IERC20(PRISMA_TOKEN).safeApprove(
            CURVE_CVXPRISMA_PRISMA_POOL,
            type(uint256).max
        );

        IERC20(PRISMA_TOKEN).safeApprove(CURVE_PRISMA_ETH_POOL, 0);
        IERC20(PRISMA_TOKEN).safeApprove(
            CURVE_PRISMA_ETH_POOL,
            type(uint256).max
        );

        IERC20(PRISMA_TOKEN).safeApprove(PRISMA_DEPOSIT, 0);
        IERC20(PRISMA_TOKEN).safeApprove(PRISMA_DEPOSIT, type(uint256).max);

        IERC20(CVXPRISMA_TOKEN).safeApprove(CURVE_CVXPRISMA_PRISMA_POOL, 0);
        IERC20(CVXPRISMA_TOKEN).safeApprove(
            CURVE_CVXPRISMA_PRISMA_POOL,
            type(uint256).max
        );

        IERC20(CVXPRISMA_TOKEN).safeApprove(vault, 0);
        IERC20(CVXPRISMA_TOKEN).safeApprove(vault, type(uint256).max);

        IERC20(CVX_TOKEN).safeApprove(CONVEX_LOCKER, 0);
        IERC20(CVX_TOKEN).safeApprove(CONVEX_LOCKER, type(uint256).max);
    }

    /// @notice Deposit from FXS
    /// @param amount - the amount of FXS to deposit
    /// @param minAmountOut - min amount of cvxFXS tokens expected
    /// @param to - address to stake on behalf of
    /// @param lock - whether to lock or swap to cvxFXS
    function depositFromPrisma(
        uint256 amount,
        uint256 minAmountOut,
        address to,
        bool lock
    ) external notToZeroAddress(to) {
        IERC20(PRISMA_TOKEN).safeTransferFrom(
            msg.sender,
            address(this),
            amount
        );
        _deposit(amount, minAmountOut, to, lock);
    }

    function _deposit(
        uint256 amount,
        uint256 minAmountOut,
        address to,
        bool lock
    ) internal {
        if (lock) {
            cvxPrismaDeposit.deposit(amount, true);
        } else {
            _swapCvxPrismaPrisma(amount, minAmountOut, false);
        }
        IGenericVault(vault).depositAll(to);
    }

    /// @notice Deposit into the pounder from ETH
    /// @param minAmountOut - min amount of lp tokens expected
    /// @param to - address to stake on behalf of
    /// @param lock - whether to lock or swap to cvxPrisma
    function depositFromEth(
        uint256 minAmountOut,
        address to,
        bool lock
    ) external payable notToZeroAddress(to) {
        require(msg.value > 0, "cheap");
        _depositFromEth(msg.value, minAmountOut, to, lock);
    }

    /// @notice Internal function to deposit ETH to the pounder
    /// @param amount - amount of ETH
    /// @param minAmountOut - min amount of lp tokens expected
    /// @param to - address to stake on behalf of
    /// @param lock - whether to lock or swap to cvxPrisma
    function _depositFromEth(
        uint256 amount,
        uint256 minAmountOut,
        address to,
        bool lock
    ) internal {
        uint256 prismaBalance = _swapEthPrisma(amount, minAmountOut, true);
        _deposit(prismaBalance, minAmountOut, to, lock);
    }

    /// @notice Deposit into the pounder from any token via Uni interface
    /// @notice Use at your own risk
    /// @dev Zap contract needs approval for spending of inputToken
    /// @param amount - min amount of input token
    /// @param minAmountOut - min amount of cvxPrisma expected
    /// @param router - address of the router to use. e.g. 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F for Sushi
    /// @param inputToken - address of the token to swap from, needs to have an ETH pair on router used
    /// @param to - address to stake on behalf of
    /// @param lock - whether to lock or swap to cvxPrisma
    function depositViaUniV2EthPair(
        uint256 amount,
        uint256 minAmountOut,
        address router,
        address inputToken,
        address to,
        bool lock
    ) external notToZeroAddress(to) {
        require(router != address(0));

        IERC20(inputToken).safeTransferFrom(msg.sender, address(this), amount);
        address[] memory _path = new address[](2);
        _path[0] = inputToken;
        _path[1] = WETH_TOKEN;

        IERC20(inputToken).safeApprove(router, 0);
        IERC20(inputToken).safeApprove(router, amount);

        IUniV2Router(router).swapExactTokensForETH(
            amount,
            1,
            _path,
            address(this),
            block.timestamp + 1
        );
        _depositFromEth(address(this).balance, minAmountOut, to, lock);
    }

    /// @notice Retrieves a user's vault shares and withdraw all
    /// @param amount - amount of shares to retrieve
    /// @return amount of underlying withdrawn
    function _claimAndWithdraw(
        uint256 amount,
        uint256 minAmountOut
    ) internal returns (uint256) {
        IERC20(vault).safeTransferFrom(msg.sender, address(this), amount);
        uint256 _cvxPrismaAmount = IGenericVault(vault).withdrawAll(
            address(this)
        );
        return _swapCvxPrismaPrisma(_cvxPrismaAmount, minAmountOut, true);
    }

    /// @notice Claim as FXS
    /// @param amount - amount to withdraw
    /// @param minAmountOut - minimum amount of underlying tokens expected
    /// @param to - address to send withdrawn underlying to
    /// @return amount of underlying withdrawn
    function claimFromVaultAsPrisma(
        uint256 amount,
        uint256 minAmountOut,
        address to
    ) public notToZeroAddress(to) returns (uint256) {
        uint256 _prismaAmount = _claimAndWithdraw(amount, minAmountOut);
        IERC20(PRISMA_TOKEN).safeTransfer(to, _prismaAmount);
        return _prismaAmount;
    }

    /// @notice Claim as native ETH
    /// @param amount - amount to withdraw
    /// @param minAmountOut - minimum amount of ETH expected
    /// @param to - address to send ETH to
    /// @return amount of ETH withdrawn
    function claimFromVaultAsEth(
        uint256 amount,
        uint256 minAmountOut,
        address to
    ) public notToZeroAddress(to) returns (uint256) {
        uint256 _ethAmount = _claimAsEth(amount, minAmountOut);
        (bool success, ) = to.call{value: _ethAmount}("");
        require(success, "ETH transfer failed");
        return _ethAmount;
    }

    /// @notice Withdraw as native ETH (internal)
    /// @param amount - amount to withdraw
    /// @param minAmountOut - minimum amount of ETH expected
    /// @return amount of ETH withdrawn
    function _claimAsEth(
        uint256 amount,
        uint256 minAmountOut
    ) public returns (uint256) {
        uint256 _prismaAmount = _claimAndWithdraw(amount, 0);
        return _swapEthPrisma(_prismaAmount, minAmountOut, false);
    }

    /// @notice Claim to any token via a univ2 router
    /// @notice Use at your own risk
    /// @param amount - amount of uFXS to unstake
    /// @param minAmountOut - min amount of output token expected
    /// @param router - address of the router to use. e.g. 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F for Sushi
    /// @param outputToken - address of the token to swap to
    /// @param to - address of the final recipient of the swapped tokens
    function claimFromVaultViaUniV2EthPair(
        uint256 amount,
        uint256 minAmountOut,
        address router,
        address outputToken,
        address to
    ) public notToZeroAddress(to) {
        require(router != address(0));
        _claimAsEth(amount, 0);
        address[] memory _path = new address[](2);
        _path[0] = WETH_TOKEN;
        _path[1] = outputToken;
        IUniV2Router(router).swapExactETHForTokens{
            value: address(this).balance
        }(minAmountOut, _path, to, block.timestamp + 1);
    }

    /// @notice Claim as USDT via Tricrypto
    /// @param amount - the amount of uFXS to unstake
    /// @param minAmountOut - the min expected amount of USDT to receive
    /// @param to - the adress that will receive the USDT
    /// @return amount of USDT obtained
    function claimFromVaultAsUsdt(
        uint256 amount,
        uint256 minAmountOut,
        address to
    ) public notToZeroAddress(to) returns (uint256) {
        uint256 _ethAmount = _claimAsEth(amount, 0);
        _swapEthToUsdt(_ethAmount, minAmountOut);
        uint256 _usdtAmount = IERC20(USDT_TOKEN).balanceOf(address(this));
        IERC20(USDT_TOKEN).safeTransfer(to, _usdtAmount);
        return _usdtAmount;
    }

    /// @notice swap ETH to USDT via Curve's tricrypto
    /// @param amount - the amount of ETH to swap
    /// @param minAmountOut - the minimum amount expected
    function _swapEthToUsdt(uint256 amount, uint256 minAmountOut) internal {
        triCryptoSwap.exchange{value: amount}(
            2, // ETH
            0, // USDT
            amount,
            minAmountOut,
            true
        );
    }

    /// @notice Claim as CVX via CurveCVX
    /// @param amount - the amount of uFXS to unstake
    /// @param minAmountOut - the min expected amount of USDT to receive
    /// @param to - the adress that will receive the CVX
    /// @param lock - whether to lock the CVX or not
    /// @return amount of CVX obtained
    function claimFromVaultAsCvx(
        uint256 amount,
        uint256 minAmountOut,
        address to,
        bool lock
    ) public notToZeroAddress(to) returns (uint256) {
        uint256 _ethAmount = _claimAsEth(amount, 0);
        uint256 _cvxAmount = _swapEthCvx(_ethAmount, minAmountOut, true);
        if (lock) {
            locker.lock(to, _cvxAmount, 0);
        } else {
            IERC20(CVX_TOKEN).safeTransfer(to, _cvxAmount);
        }
        return _cvxAmount;
    }

    modifier notToZeroAddress(address _to) {
        require(_to != address(0), "Invalid address!");
        _;
    }
}
