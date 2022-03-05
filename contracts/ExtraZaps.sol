// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "./UnionBase.sol";
import "../interfaces/ICurveTriCrypto.sol";
import "../interfaces/IUnionVault.sol";
import "../interfaces/ITriPool.sol";
import "../interfaces/IBooster.sol";
import "../interfaces/IRewards.sol";
import "../interfaces/IUniV2Router.sol";
import "../interfaces/IMerkleDistributorV2.sol";
import "../interfaces/ICVXLocker.sol";

contract ExtraZaps is Ownable, UnionBase {
    using SafeERC20 for IERC20;

    address public immutable vault;
    address private constant USDT = 0xdAC17F958D2ee523a2206206994597C13D831ec7;
    address private constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    address private constant CVX = 0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B;

    address private constant TRICRYPTO =
        0xD51a44d3FaE010294C616388b506AcdA1bfAAE46;
    address private constant TRIPOOL =
        0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7;
    address private constant TRICRV =
        0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490;
    address private constant BOOSTER =
        0xF403C135812408BFbE8713b5A23a04b3D48AAE31;
    address private constant CONVEX_TRIPOOL_TOKEN =
        0x30D9410ED1D5DA1F6C8391af5338C93ab8d4035C;
    address private constant CONVEX_TRIPOOL_REWARDS =
        0x689440f2Ff927E1f24c72F1087E1FAF471eCe1c8;
    address private constant CONVEX_LOCKER =
        0x72a19342e8F1838460eBFCCEf09F6585e32db86E;

    ICurveTriCrypto triCryptoSwap = ICurveTriCrypto(TRICRYPTO);
    ITriPool triPool = ITriPool(TRIPOOL);
    IBooster booster = IBooster(BOOSTER);
    IRewards triPoolRewards = IRewards(CONVEX_TRIPOOL_REWARDS);
    ICVXLocker locker = ICVXLocker(CONVEX_LOCKER);
    IMerkleDistributorV2 distributor;

    constructor(address _vault, address _distributor) {
        vault = _vault;
        distributor = IMerkleDistributorV2(_distributor);
    }

    function setApprovals() external {
        IERC20(TRICRV).safeApprove(BOOSTER, 0);
        IERC20(TRICRV).safeApprove(BOOSTER, type(uint256).max);

        IERC20(USDT).safeApprove(TRIPOOL, 0);
        IERC20(USDT).safeApprove(TRIPOOL, type(uint256).max);

        IERC20(CONVEX_TRIPOOL_TOKEN).safeApprove(CONVEX_TRIPOOL_REWARDS, 0);
        IERC20(CONVEX_TRIPOOL_TOKEN).safeApprove(
            CONVEX_TRIPOOL_REWARDS,
            type(uint256).max
        );

        IERC20(CRV_TOKEN).safeApprove(CURVE_CVXCRV_CRV_POOL, 0);
        IERC20(CRV_TOKEN).safeApprove(CURVE_CVXCRV_CRV_POOL, type(uint256).max);

        IERC20(CVXCRV_TOKEN).safeApprove(vault, 0);
        IERC20(CVXCRV_TOKEN).safeApprove(vault, type(uint256).max);

        IERC20(CVX).safeApprove(CONVEX_LOCKER, 0);
        IERC20(CVX).safeApprove(CONVEX_LOCKER, type(uint256).max);
    }

    /// @notice Retrieves user's uCRV and unstake to ETH
    /// @param amount - the amount of uCRV to unstake
    function _withdrawFromVaultAsEth(uint256 amount) internal {
        IERC20(vault).safeTransferFrom(msg.sender, address(this), amount);
        IUnionVault(vault).withdrawAllAs(
            address(this),
            IUnionVault.Option.ClaimAsETH
        );
    }

    /// @notice swap ETH to USDT via Curve's tricrypto
    /// @param amount - the amount of ETH to swap
    /// @param minAmountOut - the minimum amount expected
    function _swapEthToUsdt(
        uint256 amount,
        uint256 minAmountOut,
        address to
    ) internal {
        triCryptoSwap.exchange{value: amount}(
            2, // ETH
            0, // USDT
            amount,
            minAmountOut,
            true
        );
    }

    /// @notice Unstake from the Pounder to USDT
    /// @param amount - the amount of uCRV to unstake
    /// @param minAmountOut - the min expected amount of USDT to receive
    /// @param to - the adress that will receive the USDT
    /// @return amount of USDT obtained
    function claimFromVaultAsUsdt(
        uint256 amount,
        uint256 minAmountOut,
        address to
    ) public notToZeroAddress(to) returns (uint256) {
        _withdrawFromVaultAsEth(amount);
        _swapEthToUsdt(address(this).balance, minAmountOut, to);
        uint256 _usdtAmount = IERC20(USDT).balanceOf(address(this));
        if (to != address(this)) {
            IERC20(USDT).safeTransfer(to, _usdtAmount);
        }
        return _usdtAmount;
    }

    /// @notice Claim from the distributor, unstake and returns USDT.
    /// @param index - claimer index
    /// @param account - claimer account
    /// @param amount - claim amount
    /// @param merkleProof - merkle proof for the claim
    /// @param minAmountOut - the min expected amount of USDT to receive
    /// @param to - the adress that will receive the USDT
    /// @return amount of USDT obtained
    function claimFromDistributorAsUsdt(
        uint256 index,
        address account,
        uint256 amount,
        bytes32[] calldata merkleProof,
        uint256 minAmountOut,
        address to
    ) external notToZeroAddress(to) returns (uint256) {
        distributor.claim(index, account, amount, merkleProof);
        return claimFromVaultAsUsdt(amount, minAmountOut, to);
    }

    /// @notice Unstake from the Pounder to stables and stake on 3pool convex for yield
    /// @param amount - amount of uCRV to unstake
    /// @param minAmountOut - minimum amount of 3CRV (NOT USDT!)
    /// @param to - address on behalf of which to stake
    function claimFromVaultAndStakeIn3PoolConvex(
        uint256 amount,
        uint256 minAmountOut,
        address to
    ) public notToZeroAddress(to) {
        // claim as USDT
        uint256 _usdtAmount = claimFromVaultAsUsdt(amount, 0, address(this));
        // add USDT to Tripool
        triPool.add_liquidity([0, 0, _usdtAmount], minAmountOut);
        // deposit on Convex
        booster.depositAll(9, false);
        // stake on behalf of user
        triPoolRewards.stakeFor(
            to,
            IERC20(CONVEX_TRIPOOL_TOKEN).balanceOf(address(this))
        );
    }

    /// @notice Claim from the distributor, unstake and deposits in 3pool.
    /// @param index - claimer index
    /// @param account - claimer account
    /// @param amount - claim amount
    /// @param merkleProof - merkle proof for the claim
    /// @param minAmountOut - minimum amount of 3CRV (NOT USDT!)
    /// @param to - address on behalf of which to stake
    function claimFromDistributorAndStakeIn3PoolConvex(
        uint256 index,
        address account,
        uint256 amount,
        bytes32[] calldata merkleProof,
        uint256 minAmountOut,
        address to
    ) external notToZeroAddress(to) {
        distributor.claim(index, account, amount, merkleProof);
        claimFromVaultAndStakeIn3PoolConvex(amount, minAmountOut, to);
    }

    /// @notice Claim to any token via a univ2 router
    /// @notice Use at your own risk
    /// @param amount - amount of uCRV to unstake
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
        _withdrawFromVaultAsEth(amount);
        address[] memory _path = new address[](2);
        _path[0] = WETH;
        _path[1] = outputToken;
        IUniV2Router(router).swapExactETHForTokens{
            value: address(this).balance
        }(minAmountOut, _path, to, block.timestamp + 60);
    }

    /// @notice Claim to any token via a univ2 router
    /// @notice Use at your own risk
    /// @param amount - amount of uCRV to unstake
    /// @param minAmountOut - min amount of output token expected
    /// @param router - address of the router to use. e.g. 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F for Sushi
    /// @param outputToken - address of the token to swap to
    /// @param to - address of the final recipient of the swapped tokens
    function claimFromDistributorViaUniV2EthPair(
        uint256 index,
        address account,
        uint256 amount,
        bytes32[] calldata merkleProof,
        uint256 minAmountOut,
        address router,
        address outputToken,
        address to
    ) external notToZeroAddress(to) {
        distributor.claim(index, account, amount, merkleProof);
        claimFromVaultViaUniV2EthPair(
            amount,
            minAmountOut,
            router,
            outputToken,
            to
        );
    }

    /// @notice Unstake from the Pounder as CVX and locks it
    /// @param amount - amount of uCRV to unstake
    /// @param minAmountOut - min amount of CVX expected
    /// @param to - address to lock on behalf of
    function claimFromVaultAsCvxAndLock(
        uint256 amount,
        uint256 minAmountOut,
        address to
    ) public notToZeroAddress(to) {
        IERC20(vault).safeTransferFrom(msg.sender, address(this), amount);
        IUnionVault(vault).withdrawAllAs(
            address(this),
            IUnionVault.Option.ClaimAsCVX,
            minAmountOut
        );
        locker.lock(to, IERC20(CVX).balanceOf(address(this)), 0);
    }

    /// @notice Claim from the distributor, unstake to CVX and lock.
    /// @param index - claimer index
    /// @param account - claimer account
    /// @param amount - claim amount
    /// @param merkleProof - merkle proof for the claim
    /// @param minAmountOut - min amount of CVX expected
    /// @param to - address to lock on behalf of
    function claimFromDistributorAsCvxAndLock(
        uint256 index,
        address account,
        uint256 amount,
        bytes32[] calldata merkleProof,
        uint256 minAmountOut,
        address to
    ) external notToZeroAddress(to) {
        distributor.claim(index, account, amount, merkleProof);
        claimFromVaultAsCvxAndLock(amount, minAmountOut, to);
    }

    /// @notice Deposit into the pounder from ETH
    /// @param minAmountOut - min amount of cvxCRV expected
    /// @param to - address to stake on behalf of
    function depositFromEth(uint256 minAmountOut, address to)
        external
        payable
        notToZeroAddress(to)
    {
        require(msg.value > 0, "cheap");
        _depositFromEth(msg.value, minAmountOut, to);
    }

    /// @notice Internal function to deposit ETH to the pounder
    /// @param amount - amount of ETH
    /// @param minAmountOut - min amount of cvxCRV expected
    /// @param to - address to stake on behalf of
    function _depositFromEth(
        uint256 amount,
        uint256 minAmountOut,
        address to
    ) internal {
        uint256 _crvAmount = _swapEthToCrv(amount);
        uint256 _cvxCrvAmount = _swapCrvToCvxCrv(
            _crvAmount,
            address(this),
            minAmountOut
        );
        IUnionVault(vault).deposit(to, _cvxCrvAmount);
    }

    /// @notice Deposit into the pounder from CRV
    /// @param minAmountOut - min amount of cvxCRV expected
    /// @param to - address to stake on behalf of
    function depositFromCrv(
        uint256 amount,
        uint256 minAmountOut,
        address to
    ) external notToZeroAddress(to) {
        IERC20(CRV_TOKEN).safeTransferFrom(msg.sender, address(this), amount);
        uint256 _cvxCrvAmount = _swapCrvToCvxCrv(
            amount,
            address(this),
            minAmountOut
        );
        IUnionVault(vault).deposit(to, _cvxCrvAmount);
    }

    /// @notice Deposit into the pounder from any token via Uni interface
    /// @notice Use at your own risk
    /// @dev Zap contract needs approval for spending of inputToken
    /// @param amount - min amount of input token
    /// @param minAmountOut - min amount of cvxCRV expected
    /// @param router - address of the router to use. e.g. 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F for Sushi
    /// @param inputToken - address of the token to swap from, needs to have an ETH pair on router used
    /// @param to - address to stake on behalf of
    function depositViaUniV2EthPair(
        uint256 amount,
        uint256 minAmountOut,
        address router,
        address inputToken,
        address to
    ) external notToZeroAddress(to) {
        require(router != address(0));

        IERC20(inputToken).safeTransferFrom(msg.sender, address(this), amount);
        address[] memory _path = new address[](2);
        _path[0] = inputToken;
        _path[1] = WETH;

        IERC20(inputToken).safeApprove(router, 0);
        IERC20(inputToken).safeApprove(router, amount);

        IUniV2Router(router).swapExactTokensForETH(
            amount,
            1,
            _path,
            address(this),
            block.timestamp + 1
        );
        _depositFromEth(address(this).balance, minAmountOut, to);
    }

    /// @notice Execute calls on behalf of contract
    /// (for instance to retrieve locked tokens)
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
