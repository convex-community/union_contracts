// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

interface IMerkleDrop {
    function claim(
        bytes32[] calldata _proof,
        address _who,
        uint256 _amount
    ) external;
}

contract EPSClaim is Ownable {
    using SafeERC20 for IERC20;
    address private constant EPS = 0xA7f552078dcC247C2684336020c03648500C6d9F;

    struct claimParam {
        address claimContract;
        address owner;
        uint256 amount;
        bytes32[] merkleProof;
    }

    function claim(claimParam[] calldata claimParams, address to)
        external
        onlyOwner
    {
        require(to != address(0));
        for (uint256 i; i < claimParams.length; ++i) {
            IMerkleDrop(claimParams[i].claimContract).claim(
                claimParams[i].merkleProof,
                claimParams[i].owner,
                claimParams[i].amount
            );
        }
        IERC20(EPS).safeTransfer(to, IERC20(EPS).balanceOf(address(this)));
    }

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
