// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "../interfaces/IMultiMerkleStash.sol";
import "../interfaces/IMerkleDistributorV2.sol";
import "../interfaces/IUniV2Router.sol";
import "../interfaces/IWETH.sol";
import "../interfaces/ICvxCrvDeposit.sol";
import "../interfaces/IVotiumRegistry.sol";
import "../interfaces/IUniV3Router.sol";
import "./UnionBase.sol";

contract UnionZap is Ownable, UnionBase {
    using SafeERC20 for IERC20;

    address public votiumDistributor =
        0x378Ba9B73309bE80BF4C2c027aAD799766a7ED5A;
    address public unionDistributor;

    address private constant SUSHI_ROUTER =
        0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F;
    address private constant UNISWAP_ROUTER =
        0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    address private constant UNIV3_ROUTER =
        0xE592427A0AEce92De3Edee1F18E0157C05861564;
    address private constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    address private constant CVXCRV_DEPOSIT =
        0x8014595F2AB54cD7c604B00E9fb932176fDc86Ae;
    address public constant VOTIUM_REGISTRY =
        0x92e6E43f99809dF84ed2D533e1FD8017eb966ee2;

    uint256 private constant BASE_TX_GAS = 21000;
    uint256 private constant FINAL_TRANSFER_GAS = 50000;

    uint256 public unionDues = 200;
    uint256 public constant FEE_DENOMINATOR = 10000;
    uint256 public constant MAX_DUES = 400;

    mapping(uint256 => address) private routers;
    mapping(uint256 => uint24) private fees;

    struct claimParam {
        address token;
        uint256 index;
        uint256 amount;
        bytes32[] merkleProof;
    }

    event Received(address sender, uint256 amount);
    event Distributed(uint256 amount, uint256 fees, bool locked);
    event DistributorUpdated(address distributor);
    event VotiumDistributorUpdated(address distributor);
    event DuesUpdated(uint256 dues);
    event FundsRetrieved(address token, address to, uint256 amount);

    constructor(address distributor_) {
        unionDistributor = distributor_;
        routers[0] = SUSHI_ROUTER;
        routers[1] = UNISWAP_ROUTER;
        fees[0] = 3000;
        fees[1] = 10000;
    }

    /// @notice Update union fees
    /// @param dues - Fees taken from the collected bribes in bips
    function setUnionDues(uint256 dues) external onlyOwner {
        require(dues <= MAX_DUES, "Dues too high");
        unionDues = dues;
        emit DuesUpdated(dues);
    }

    /// @notice Update the contract used to distribute funds
    /// @param distributor_ - Address of the new contract
    function updateDistributor(address distributor_) external onlyOwner {
        require(distributor_ != address(0));
        unionDistributor = distributor_;
        emit DistributorUpdated(distributor_);
    }

    /// @notice Change forwarding address in Votium registry
    /// @param _to - address that will be forwarded to
    /// @dev To be used in case of migration, rewards can be forwarded to
    /// new contracts
    function setForwarding(address _to) external onlyOwner {
        IVotiumRegistry(VOTIUM_REGISTRY).setRegistry(_to);
    }

    /// @notice Update the votium contract address to claim for
    /// @param distributor_ - Address of the new contract
    function updateVotiumDistributor(address distributor_) external onlyOwner {
        require(distributor_ != address(0));
        votiumDistributor = distributor_;
        emit VotiumDistributorUpdated(distributor_);
    }

    /// @notice Withdraws specified ERC20 tokens to the multisig
    /// @param tokens - the tokens to retrieve
    /// @param to - address to send the tokens to
    /// @dev This is needed to handle tokens that don't have ETH pairs on sushi
    /// or need to be swapped on other chains (NBST, WormholeLUNA...)
    function retrieveTokens(address[] calldata tokens, address to)
        external
        onlyOwner
    {
        require(to != address(0));
        for (uint256 i; i < tokens.length; ++i) {
            address token = tokens[i];
            uint256 tokenBalance = IERC20(token).balanceOf(address(this));
            IERC20(token).safeTransfer(to, tokenBalance);
            emit FundsRetrieved(token, to, tokenBalance);
        }
    }

    /// @notice Execute calls on behalf of contract in case of emergency
    function execute(
        address _to,
        uint256 _value,
        bytes calldata _data
    ) external onlyOwner returns (bool, bytes memory) {
        (bool success, bytes memory result) = _to.call{value: _value}(_data);
        return (success, result);
    }

    /// @notice Set approvals for the tokens used when swapping
    function setApprovals() external onlyOwner {
        IERC20(CRV_TOKEN).safeApprove(CURVE_CVXCRV_CRV_POOL, 0);
        IERC20(CRV_TOKEN).safeApprove(CURVE_CVXCRV_CRV_POOL, type(uint256).max);

        IERC20(CRV_TOKEN).safeApprove(CVXCRV_DEPOSIT, 0);
        IERC20(CRV_TOKEN).safeApprove(CVXCRV_DEPOSIT, type(uint256).max);

        IERC20(CVXCRV_TOKEN).safeApprove(CVXCRV_STAKING_CONTRACT, 0);
        IERC20(CVXCRV_TOKEN).safeApprove(
            CVXCRV_STAKING_CONTRACT,
            type(uint256).max
        );
    }

    /// @notice Swap a token for ETH
    /// @param token - address of the token to swap
    /// @param amount - amount of the token to swap
    /// @dev Swaps are executed via Sushi or UniV2 router, will revert if pair
    /// does not exist. Tokens must have a WETH pair.
    function _swapToETH(
        address token,
        uint256 amount,
        address router
    ) internal {
        require(router != address(0));
        address[] memory _path = new address[](2);
        _path[0] = token;
        _path[1] = WETH;

        IERC20(token).safeApprove(router, 0);
        IERC20(token).safeApprove(router, amount);

        IUniV2Router(router).swapExactTokensForETH(
            amount,
            1,
            _path,
            address(this),
            block.timestamp + 1
        );
    }

    /// @notice Swap a token for ETH on UniSwap V3
    /// @param token - address of the token to swap
    /// @param amount - amount of the token to swap
    /// @param fee - the pool's fee
    function _swapToETHUniV3(
        address token,
        uint256 amount,
        uint24 fee
    ) internal {
        IERC20(token).safeApprove(UNIV3_ROUTER, 0);
        IERC20(token).safeApprove(UNIV3_ROUTER, amount);
        IUniV3Router.ExactInputSingleParams memory _params = IUniV3Router
            .ExactInputSingleParams(
                token,
                WETH,
                fee,
                address(this),
                block.timestamp + 1,
                amount,
                1,
                0
            );
        uint256 _wethReceived = IUniV3Router(UNIV3_ROUTER).exactInputSingle(
            _params
        );
        IWETH(WETH).withdraw(_wethReceived);
    }

    /// @notice Claims all specified rewards from Votium
    /// @param claimParams - an array containing the info necessary to claim for
    /// each available token
    /// @dev Used to retrieve tokens that need to be transferred
    function claim(IMultiMerkleStash.claimParam[] calldata claimParams)
        public
        onlyOwner
    {
        require(claimParams.length > 0, "No claims");
        // claim all from votium
        IMultiMerkleStash(votiumDistributor).claimMulti(
            address(this),
            claimParams
        );
    }

    /// @notice Claims all specified rewards and swaps them to ETH
    /// @param claimParams - an array containing the info necessary to claim
    /// @param routerChoices - the router to use for the swap
    /// @param claimBeforeSwap - whether to claim on Votium or not
    /// @param lock - whether to lock or swap crv to cvxcrv
    /// @param stake - whether to stake cvxcrv (if distributor is vault)
    /// @param minAmountOut - min output amount of cvxCRV or CRV (if locking)
    /// @dev routerChoices is a 2-bit bitmap such that
    /// 0b00 (0) - Sushi
    /// 0b01 (1) - UniV2
    /// 0b10 (2) - UniV3 0.3%
    /// 0b11 (3) - UniV3 1%
    /// Ex: 6 = 00 01 10 will swap token 1 on UniV3, 2 on UniV3, last on Sushi
    /// Passing 0 will execute all swaps on sushi
    /// @dev claimBeforeSwap is used in case 3rd party already claimed on Votium
    function _distribute(
        IMultiMerkleStash.claimParam[] calldata claimParams,
        uint256 routerChoices,
        bool claimBeforeSwap,
        bool lock,
        bool stake,
        uint256 minAmountOut
    ) internal {
        // initialize gas counting
        uint256 _startGas = gasleft();
        bool _locked = false;

        // claim
        if (claimBeforeSwap) {
            claim(claimParams);
        }

        // swap all claims to ETH
        for (uint256 i; i < claimParams.length; ++i) {
            address _token = claimParams[i].token;
            uint256 _balance = IERC20(_token).balanceOf(address(this));
            // avoid wasting gas / reverting if no balance
            if (_balance <= 1) {
                continue;
            } else {
                // leave one gwei to lower future claim gas costs
                // https://twitter.com/libevm/status/1474870670429360129?s=21
                _balance -= 1;
            }
            // unwrap WETH
            if (_token == WETH) {
                IWETH(WETH).withdraw(_balance);
            }
            // no need to swap bribes paid out in cvxCRV or CRV
            else if ((_token == CRV_TOKEN) || (_token == CVXCRV_TOKEN)) {
                continue;
            } else {
                uint256 _choice = routerChoices & 3;
                if (_choice >= 2) {
                    _swapToETHUniV3(_token, _balance, fees[_choice - 2]);
                } else {
                    _swapToETH(_token, _balance, routers[_choice]);
                }
            }
            routerChoices = routerChoices >> 2;
        }

        uint256 _ethBalance = address(this).balance;

        // if locking, we apply minAmount to CRV - otherwise will do on cvxCRV
        uint256 minCrvOut = lock ? minAmountOut : 0;
        // swap from ETH to CRV
        uint256 _swappedCrv = _swapEthToCrv(_ethBalance, minCrvOut);

        uint256 _crvBalance = IERC20(CRV_TOKEN).balanceOf(address(this));

        // swap on Curve if there is a premium for doing so
        if (!lock) {
            _swapCrvToCvxCrv(_crvBalance, address(this), minAmountOut);
        }
        // otherwise deposit & lock
        else {
            ICvxCrvDeposit(CVXCRV_DEPOSIT).deposit(_crvBalance, true);
            _locked = true;
        }

        uint256 _cvxCrvBalance = IERC20(CVXCRV_TOKEN).balanceOf(address(this));

        // freeze distributor before transferring funds
        IMerkleDistributorV2(unionDistributor).freeze();

        // estimate gas cost
        uint256 _gasUsed = _startGas -
            gasleft() +
            BASE_TX_GAS +
            16 *
            msg.data.length +
            FINAL_TRANSFER_GAS;
        // compute the ETH/CRV exchange rate based on previous curve swap
        uint256 _gasCostInCrv = (_gasUsed * tx.gasprice * _swappedCrv) /
            _ethBalance;
        uint256 _fees = (_cvxCrvBalance * unionDues) / FEE_DENOMINATOR;
        uint256 _netDeposit = _cvxCrvBalance - _fees - _gasCostInCrv;

        // transfer funds
        IERC20(CVXCRV_TOKEN).safeTransfer(unionDistributor, _netDeposit);
        if (stake) {
            IMerkleDistributorV2(unionDistributor).stake();
        }
        emit Distributed(_netDeposit, _cvxCrvBalance - _netDeposit, _locked);
    }

    /// @notice External wrapper around _distribute
    /// @param claimParams - an array containing the info necessary to claim
    /// @param routerChoices - the router to use for the swap
    /// @param claimBeforeSwap - whether to claim on Votium or not
    /// @param lock - whether to lock or swap crv to cvxcrv
    /// @param stake - whether to stake cvxcrv (if distributor is vault)
    /// @param minAmountOut - min output amount of cvxCRV or CRV (if locking)
    function distribute(
        IMultiMerkleStash.claimParam[] calldata claimParams,
        uint256 routerChoices,
        bool claimBeforeSwap,
        bool lock,
        bool stake,
        uint256 minAmountOut
    ) external onlyOwner {
        _distribute(
            claimParams,
            routerChoices,
            claimBeforeSwap,
            lock,
            stake,
            minAmountOut
        );
    }

    // @notice Stakes the accumulated cvxCrv for the owner
    function stakeAccumulated() external onlyOwner {
        cvxCrvStaking.stakeFor(
            owner(),
            IERC20(CVXCRV_TOKEN).balanceOf(address(this)) - 1
        );
    }

    // @notice retrieves part of the cvxCRV and transfers it to a wallet
    // @param amount - the amount to claim
    // @param to - the address to send the cvxCRV to
    function claimAccumulated(uint256 amount, address to) external onlyOwner {
        require(to != address(0));
        IERC20(CVXCRV_TOKEN).safeTransfer(to, amount);
    }

    receive() external payable {
        emit Received(msg.sender, msg.value);
    }
}
