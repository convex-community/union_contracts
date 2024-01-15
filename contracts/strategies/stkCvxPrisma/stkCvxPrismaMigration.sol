// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "../../../interfaces/IGenericVault.sol";
import "../../../interfaces/IUnionVault.sol";
import "../../../../node_modules/hardhat/console.sol";

interface ICvxPrismaStaking {
    function withdraw(uint256) external;
}

contract stkCvxPrismaMigration {
    using SafeERC20 for IERC20;

    address private constant STKCVXPRISMA_TOKEN =
        0x0c73f1cFd5C9dFc150C8707Aa47Acbd14F0BE108;

    address private constant UNION_PRISMA_VAULT =
        0x9bfD08D7b3cC40129132A17b4d5B9Ea3351464BD;

    address private constant CVXPRISMA_TOKEN =
        0x34635280737b5BFe6c7DC2FC3065D60d66e78185;

    address public vault;

    constructor(address _vault) {
        require(_vault != address(0));
        vault = _vault;
    }

    /// @notice Set approvals for the contracts used when swapping & staking
    function setApprovals() external {
        IERC20(CVXPRISMA_TOKEN).safeApprove(vault, 0);
        IERC20(CVXPRISMA_TOKEN).safeApprove(vault, type(uint256).max);
    }

    function migrate(uint256 amount, address to) external {
        IERC20(STKCVXPRISMA_TOKEN).safeTransferFrom(
            msg.sender,
            address(this),
            amount
        );
        console.log(IERC20(STKCVXPRISMA_TOKEN).balanceOf(address(this)));
        ICvxPrismaStaking(STKCVXPRISMA_TOKEN).withdraw(amount);
        IGenericVault(vault).depositAll(to);
    }

    receive() external payable {}
}
