// SPDX-License-Identifier: MIT
// https://etherscan.io/address/0xcbe6b83e77cdc011cc18f6f0df8444e5783ed982#code
pragma solidity 0.8.9;

import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/utils/cryptography/MerkleProof.sol";
import "./ClaimZaps.sol";
import "../interfaces/IUnionVault.sol";

// Allows anyone to claim a token if they exist in a merkle root.
contract MerkleDistributorV2 is ClaimZaps {
    using SafeERC20 for IERC20;

    address public vault;
    bytes32 public merkleRoot;
    uint32 public week;
    bool public frozen;

    address public admin;
    address public depositor;

    // This is a packed array of booleans.
    mapping(uint256 => mapping(uint256 => uint256)) private claimedBitMap;

    // This event is triggered whenever a call to #claim succeeds.
    event Claimed(
        uint256 index,
        uint256 indexed amount,
        address indexed account,
        uint256 week
    );
    // This event is triggered whenever the merkle root gets updated.
    event MerkleRootUpdated(bytes32 indexed merkleRoot, uint32 indexed week);
    // This event is triggered whenever the admin is updated.
    event AdminUpdated(address indexed oldAdmin, address indexed newAdmin);
    // This event is triggered whenever the depositor contract is updated.
    event DepositorUpdated(
        address indexed oldDepositor,
        address indexed newDepositor
    );

    constructor(address _vault, address _depositor) {
        require(_vault != address(0));
        vault = _vault;
        admin = msg.sender;
        depositor = _depositor;
        week = 0;
        frozen = true;
    }

    /// @notice Set approvals for the tokens used when swapping
    function setApprovals() external onlyAdmin {
        _setApprovals();
        IERC20(CVXCRV_TOKEN).safeApprove(vault, 0);
        IERC20(CVXCRV_TOKEN).safeApprove(vault, type(uint256).max);
    }

    /// @notice Check if the index has been marked as claimed.
    /// @param index - the index to check
    /// @return true if index has been marked as claimed.
    function isClaimed(uint256 index) public view returns (bool) {
        uint256 claimedWordIndex = index / 256;
        uint256 claimedBitIndex = index % 256;
        uint256 claimedWord = claimedBitMap[week][claimedWordIndex];
        uint256 mask = (1 << claimedBitIndex);
        return claimedWord & mask == mask;
    }

    function _setClaimed(uint256 index) private {
        uint256 claimedWordIndex = index / 256;
        uint256 claimedBitIndex = index % 256;
        claimedBitMap[week][claimedWordIndex] =
            claimedBitMap[week][claimedWordIndex] |
            (1 << claimedBitIndex);
    }

    /// @notice Transfers ownership of the contract
    /// @param newAdmin - address of the new admin of the contract
    function updateAdmin(address newAdmin) external onlyAdmin {
        require(newAdmin != address(0));
        address oldAdmin = admin;
        admin = newAdmin;
        emit AdminUpdated(oldAdmin, newAdmin);
    }

    /// @notice Changes the contract allowed to freeze before depositing
    /// @param newDepositor - address of the new depositor contract
    function updateDepositor(address newDepositor) external onlyAdmin {
        require(newDepositor != address(0));
        address oldDepositor = depositor;
        depositor = newDepositor;
        emit DepositorUpdated(oldDepositor, newDepositor);
    }

    /// @notice Internal function to handle users' claims
    /// @param index - claimer index
    /// @param account - claimer account
    /// @param amount - claim amount
    /// @param merkleProof - merkle proof for the claim
    function _claim(
        uint256 index,
        address account,
        uint256 amount,
        bytes32[] calldata merkleProof
    ) internal {
        require(!frozen, "Claiming is frozen.");
        require(!isClaimed(index), "Drop already claimed.");

        // Verify the merkle proof.
        bytes32 node = keccak256(abi.encodePacked(index, account, amount));
        require(
            MerkleProof.verify(merkleProof, merkleRoot, node),
            "Invalid proof."
        );

        // Mark it claimed and send the token.
        _setClaimed(index);
    }

    /// @notice Claim the given amount of uCRV to the given address.
    /// @param index - claimer index
    /// @param account - claimer account
    /// @param amount - claim amount
    /// @param merkleProof - merkle proof for the claim
    function claim(
        uint256 index,
        address account,
        uint256 amount,
        bytes32[] calldata merkleProof
    ) external {
        // Claim
        _claim(index, account, amount, merkleProof);

        // Send shares to account
        IERC20(vault).safeTransfer(account, amount);

        emit Claimed(index, amount, account, week);
    }

    /// @notice Claim as an other token
    /// Reverts if the inputs are invalid.
    /// @param index - claimer index
    /// @param account - claimer account
    /// @param amount - claim amount
    /// @param merkleProof - merkle proof for the claim
    /// @param option - claiming option
    function claimAs(
        uint256 index,
        address account,
        uint256 amount,
        bytes32[] calldata merkleProof,
        Option option
    ) external {
        _claimZap(index, account, amount, merkleProof, option, 0);
    }

    /// @notice Claim as an other token
    /// Reverts if the inputs are invalid.
    /// @param index - claimer index
    /// @param account - claimer account
    /// @param amount - claim amount
    /// @param merkleProof - merkle proof for the claim
    /// @param option - claiming option
    /// @param minAmountOut - minimum desired amount of output token
    function claimAs(
        uint256 index,
        address account,
        uint256 amount,
        bytes32[] calldata merkleProof,
        Option option,
        uint256 minAmountOut
    ) external {
        _claimZap(index, account, amount, merkleProof, option, minAmountOut);
    }

    /// @notice Claim as an other token
    /// Reverts if the inputs are invalid.
    /// @param index - claimer index
    /// @param account - claimer account
    /// @param amount - claim amount
    /// @param merkleProof - merkle proof for the claim
    /// @param option - claiming option
    /// @param minAmountOut - minimum desired amount of output token
    function _claimZap(
        uint256 index,
        address account,
        uint256 amount,
        bytes32[] calldata merkleProof,
        Option option,
        uint256 minAmountOut
    ) internal {
        // Claim
        _claim(index, account, amount, merkleProof);

        // Unstake
        uint256 _withdrawn = IUnionVault(vault).withdraw(address(this), amount);

        // Claim it as the specified token
        _claimAs(account, _withdrawn, option, minAmountOut);
        emit Claimed(index, amount, account, week);
    }

    /// @notice Stakes the contract's entire cvxCRV balance in the Vault
    function stake() external onlyAdminOrDistributor {
        IUnionVault(vault).depositAll(address(this));
    }

    /// @notice Freezes the claim function to allow the merkleRoot to be changed
    /// @dev Can be called by the owner or the depositor zap contract
    function freeze() external onlyAdminOrDistributor {
        frozen = true;
    }

    /// @notice Unfreezes the claim function.
    function unfreeze() public onlyAdmin {
        frozen = false;
    }

    /// @notice Update the merkle root and increment the week.
    /// @param _merkleRoot - the new root to push
    /// @param _unfreeze - whether to unfreeze the contract after unlock
    function updateMerkleRoot(bytes32 _merkleRoot, bool _unfreeze)
        external
        onlyAdmin
    {
        require(frozen, "Contract not frozen.");

        // Increment the week (simulates the clearing of the claimedBitMap)
        week = week + 1;
        // Set the new merkle root
        merkleRoot = _merkleRoot;

        emit MerkleRootUpdated(merkleRoot, week);

        if (_unfreeze) {
            unfreeze();
        }
    }

    receive() external payable {}

    modifier onlyAdmin() {
        require(msg.sender == admin, "Admin only");
        _;
    }

    modifier onlyAdminOrDistributor() {
        require(
            (msg.sender == admin) || (msg.sender == depositor),
            "Admin or depositor only"
        );
        _;
    }
}
