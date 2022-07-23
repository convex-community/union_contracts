// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "../../../interfaces/IBasicRewards.sol";
import "../../../interfaces/balancer/IBalancer.sol";
import "../../../interfaces/balancer/IAsset.sol";

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
    address public constant WSTETH_TOKEN =
        0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0;
    address public constant AURA_TOKEN =
        0xC0c293ce456fF0ED870ADd98a0828Dd4d2903DBF;
    address public constant BBUSD_TOKEN =
        0x7B50775383d3D6f0215A8F290f2C9e2eEBBEceb2;

    bytes32 private constant WSTETH_WETH_POOL_ID =
        0x32296969ef14eb0c6d29669c550d4a0449130230000200000000000000000080;
    bytes32 private constant WSTETH_BBUSD_POOL_ID =
        0x5a6a8cffb4347ff7fc484bf5f0f8a2e234d34255000200000000000000000275;
    bytes32 private constant AURA_ETH_POOL_ID =
        0xcfca23ca9ca720b6e98e3eb9b6aa0ffc4a5c08b9000200000000000000000274;

    uint256 private WSTETH_WETH_POOL_WSTETH_INDEX = 0;
    uint256 private WSTETH_WETH_POOL_WETH_INDEX = 1;
    uint256 private WSTETH_BBUSD_POOL_WSTETH_INDEX = 1;
    uint256 private WSTETH_BBUSD_POOL_BBUSD_INDEX = 2;

    IBasicRewards public auraBalStaking = IBasicRewards(AURABAL_STAKING);
    IBalancerVault public balVault = IBalancerVault(BAL_VAULT);

    /// @notice Swap Aura for WETH on Balancer
    /// @param amount - amount to swap
    /// @param minAmountOut - minimum acceptable output amount of tokens
    /// @return amount of WETH obtained after the swap
    function _swapAuraToWEth(uint256 amount, uint256 minAmountOut)
        internal
        returns (uint256)
    {
        IBalancerVault.SingleSwap memory auraSwapParams = IBalancerVault
            .SingleSwap({
                poolId: AURA_ETH_POOL_ID,
                kind: IBalancerVault.SwapKind.GIVEN_IN,
                assetIn: IAsset(AURA_TOKEN),
                assetOut: IAsset(WETH_TOKEN),
                amount: amount,
                userData: new bytes(0)
            });
        IBalancerVault.FundManagement memory funds = IBalancerVault
            .FundManagement({
                sender: address(this),
                fromInternalBalance: false,
                recipient: payable(address(this)),
                toInternalBalance: false
            });
        return
            balVault.swap(
                auraSwapParams,
                funds,
                minAmountOut,
                block.timestamp + 1
            );
    }

    /// @notice Swap bb-USD for WETH on Balancer via wstEth
    /// @param amount - amount to swap
    /// @return amount of WETH obtained after the swap
    function _swapBbUsdToWEth(uint256 amount) internal returns (uint256) {
        IBalancerVault.BatchSwapStep[]
            memory swaps = new IBalancerVault.BatchSwapStep[](2);
        swaps[0] = IBalancerVault.BatchSwapStep({
            poolId: WSTETH_BBUSD_POOL_ID,
            assetInIndex: WSTETH_BBUSD_POOL_BBUSD_INDEX,
            assetOutIndex: WSTETH_BBUSD_POOL_WSTETH_INDEX,
            amount: amount,
            userData: new bytes(0)
        });
        swaps[1] = IBalancerVault.BatchSwapStep({
            poolId: WSTETH_WETH_POOL_ID,
            assetInIndex: WSTETH_WETH_POOL_WSTETH_INDEX,
            assetOutIndex: WSTETH_WETH_POOL_WETH_INDEX,
            amount: 0,
            userData: new bytes(0)
        });
        IBalancerVault.FundManagement memory funds = IBalancerVault
            .FundManagement({
                sender: address(this),
                fromInternalBalance: false,
                recipient: payable(address(this)),
                toInternalBalance: false
            });
        IAsset[] memory zapAssets = [
            IAsset(BBUSD_TOKEN),
            IAsset(WSTETH_TOKEN),
            IAsset(WETH_TOKEN)
        ];
        int256[] memory limits = [
            int256(amount),
            type(int256).max,
            type(int256).max
        ];

        return
            balVault.batchSwap(
                IBalancerVault.SwapKind.GIVEN_IN,
                swaps,
                zapAssets,
                funds,
                limits,
                block.timestamp + 1
            );
    }

    receive() external payable {}
}
