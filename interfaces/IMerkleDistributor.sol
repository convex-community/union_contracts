// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

interface IMerkleDistributor {
    enum Option {
        Claim,
        ClaimAsETH,
        ClaimAsCRV,
        ClaimAsCVX,
        ClaimAndStake
    }

    function token() external view returns (address);

    function merkleRoot() external view returns (bytes32);

    function week() external view returns (uint32);

    function frozen() external view returns (bool);

    function isClaimed(uint256 index) external view returns (bool);

    function setApprovals() external;

    function claim(
        uint256 index,
        address account,
        uint256 amount,
        bytes32[] calldata merkleProof,
        Option option
    ) external;

    function freeze() external;

    function unfreeze() external;

    function updateMerkleRoot(bytes32 newMerkleRoot) external;

    event Claimed(
        uint256 index,
        uint256 amount,
        address indexed account,
        uint256 indexed week,
        Option option
    );
    event MerkleRootUpdated(bytes32 indexed merkleRoot, uint32 indexed week);
}
