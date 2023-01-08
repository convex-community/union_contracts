// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "../../../../interfaces/IVaultRewardHandler.sol";

contract stkCvxCrvHandlerBase is IVaultRewardHandler {
    using SafeERC20 for IERC20;
    address public owner;
    uint256 public allowedSlippage = 9500;
    uint256 public constant DECIMALS = 10000;
    address public pendingOwner;

    address public constant WETH_TOKEN =
        0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;

    constructor() {
        owner = msg.sender;
    }

    function setPendingOwner(address _po) external onlyOwner {
        pendingOwner = _po;
    }

    function applyPendingOwner() external onlyOwner {
        require(pendingOwner != address(0), "invalid owner");
        owner = pendingOwner;
        pendingOwner = address(0);
    }

    function rescueToken(address _token, address _to) external onlyOwner {
        uint256 _balance = IERC20(_token).balanceOf(address(this));
        IERC20(_token).safeTransfer(_to, _balance);
    }

    function setSlippage(uint256 _slippage) external onlyOwner {
        allowedSlippage = _slippage;
    }

    function sell(uint256 _amount) external virtual {}

    modifier onlyOwner() {
        require((msg.sender == owner), "owner only");
        _;
    }

    receive() external payable {}
}
