// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "../../../interfaces/IBasicRewards.sol";
import "../../../interfaces/balancer/IBalancer.sol";
import "../../../interfaces/balancer/IAsset.sol";
import "../../../interfaces/balancer/IBalPtDeposit.sol";

contract AuraBalStrategyBase {
    address public constant AURABAL_PT_DEPOSIT =
        0xeAd792B55340Aa20181A80d6a16db6A0ECd1b827;
    address public constant AURABAL_STAKING =
        0x5e5ea2048475854a5702F5B8468A51Ba1296EFcC;
    address public constant BAL_VAULT =
        0xBA12222222228d8Ba445958a75a0704d566BF2C8;

    address public constant AURABAL_TOKEN =
        0x616e8BfA43F920657B3497DBf40D6b1A02D4608d;
    address public constant WETH_TOKEN =
        0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    address public constant AURA_TOKEN =
        0xC0c293ce456fF0ED870ADd98a0828Dd4d2903DBF;
    address public constant BAL_TOKEN =
        0xba100000625a3754423978a60c9317c58a424e3D;
    address public constant BBUSD_TOKEN =
        0x7B50775383d3D6f0215A8F290f2C9e2eEBBEceb2;
    address public constant BBUSDC_TOKEN =
        0x9210F1204b5a24742Eba12f710636D76240dF3d0;
    address public constant USDC_TOKEN =
        0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48;
    address public constant BAL_ETH_POOL_TOKEN =
        0x5c6Ee304399DBdB9C8Ef030aB642B10820DB8F56;

    bytes32 private constant BBUSD_AAVE_POOL_ID =
        0x7b50775383d3d6f0215a8f290f2c9e2eebbeceb20000000000000000000000fe;
    bytes32 private constant BBUSDC_USDC_POOL_ID =
        0x9210f1204b5a24742eba12f710636d76240df3d00000000000000000000000fc;
    bytes32 private constant ETH_USDC_POOL_ID =
        0x96646936b91d6b9d7d0c47c496afbf3d6ec7b6f8000200000000000000000019;
    bytes32 private constant AURA_ETH_POOL_ID =
        0xcfca23ca9ca720b6e98e3eb9b6aa0ffc4a5c08b9000200000000000000000274;
    bytes32 private constant BAL_ETH_POOL_ID =
        0x5c6ee304399dbdb9c8ef030ab642b10820db8f56000200000000000000000014;

    uint256 private WSTETH_WETH_POOL_WSTETH_INDEX = 0;
    uint256 private WSTETH_WETH_POOL_WETH_INDEX = 1;
    uint256 private WSTETH_BBUSD_POOL_WSTETH_INDEX = 1;
    uint256 private WSTETH_BBUSD_POOL_BBUSD_INDEX = 2;

    IBasicRewards public auraBalStaking = IBasicRewards(AURABAL_STAKING);
    IBalancerVault public balVault = IBalancerVault(BAL_VAULT);
    IBalPtDeposit public bptDepositor = IBalPtDeposit(AURABAL_PT_DEPOSIT);

    /// @notice Swap Aura for WETH on Balancer
    /// @param _amount - amount to swap
    /// @param _minAmountOut - minimum acceptable output amount of tokens
    /// @return amount of WETH obtained after the swap
    function _swapAuraToWEth(uint256 _amount, uint256 _minAmountOut)
        internal
        returns (uint256)
    {
        IBalancerVault.SingleSwap memory _auraSwapParams = IBalancerVault
            .SingleSwap({
                poolId: AURA_ETH_POOL_ID,
                kind: IBalancerVault.SwapKind.GIVEN_IN,
                assetIn: IAsset(AURA_TOKEN),
                assetOut: IAsset(WETH_TOKEN),
                amount: _amount,
                userData: new bytes(0)
            });

        return
            balVault.swap(
                _auraSwapParams,
                _createSwapFunds(),
                _minAmountOut,
                block.timestamp + 1
            );
    }

    /// @notice Swap bb-USD for WETH on Balancer via wstEth
    /// @param _amount - amount to swap
    function _swapBbUsdToWEth(uint256 _amount) internal {
        IBalancerVault.BatchSwapStep[]
            memory _swaps = new IBalancerVault.BatchSwapStep[](3);
        _swaps[0] = IBalancerVault.BatchSwapStep({
            poolId: BBUSD_AAVE_POOL_ID,
            assetInIndex: 0,
            assetOutIndex: 1,
            amount: _amount,
            userData: new bytes(0)
        });
        _swaps[1] = IBalancerVault.BatchSwapStep({
            poolId: BBUSDC_USDC_POOL_ID,
            assetInIndex: 1,
            assetOutIndex: 2,
            amount: 0,
            userData: new bytes(0)
        });
        _swaps[2] = IBalancerVault.BatchSwapStep({
            poolId: ETH_USDC_POOL_ID,
            assetInIndex: 1,
            assetOutIndex: 0,
            amount: 0,
            userData: new bytes(0)
        });

        IAsset[] memory _zapAssets = new IAsset[](3);
        int256[] memory _limits = new int256[](3);

        _zapAssets[0] = IAsset(BBUSD_TOKEN);
        _zapAssets[1] = IAsset(BBUSDC_TOKEN);
        _zapAssets[2] = IAsset(USDC_TOKEN);
        _zapAssets[3] = IAsset(WETH_TOKEN);

        _limits[0] = int256(_amount);
        _limits[1] = type(int256).max;
        _limits[2] = type(int256).max;
        _limits[3] = type(int256).max;

        balVault.batchSwap(
            IBalancerVault.SwapKind.GIVEN_IN,
            _swaps,
            _zapAssets,
            _createSwapFunds(),
            _limits,
            block.timestamp + 1
        );
    }

    /// @notice Deposit BAL and WETH to the BAL-ETH pool
    /// @param _wethAmount - amount of wETH to deposit
    /// @param _balAmount - amount of BAL to deposit
    /// @param _minAmountOut - min amount of BPT expected
    function _depositToBalEthPool(
        uint256 _balAmount,
        uint256 _wethAmount,
        uint256 _minAmountOut
    ) internal {
        IAsset[] memory _assets = new IAsset[](2);
        _assets[0] = IAsset(BAL_TOKEN);
        _assets[1] = IAsset(WETH_TOKEN);

        uint256[] memory _amountsIn = new uint256[](2);
        _amountsIn[0] = _balAmount;
        _amountsIn[1] = _wethAmount;

        balVault.joinPool(
            BAL_ETH_POOL_ID,
            address(this),
            address(this),
            IBalancerVault.JoinPoolRequest(
                _assets,
                _amountsIn,
                abi.encode(
                    JoinKind.EXACT_TOKENS_IN_FOR_BPT_OUT,
                    _amountsIn,
                    _minAmountOut
                ),
                false
            )
        );
    }

    function _createSwapFunds()
        internal
        returns (IBalancerVault.FundManagement memory)
    {
        return
            IBalancerVault.FundManagement({
                sender: address(this),
                fromInternalBalance: false,
                recipient: payable(address(this)),
                toInternalBalance: false
            });
    }

    receive() external payable {}
}
