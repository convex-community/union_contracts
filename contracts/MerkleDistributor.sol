// SPDX-License-Identifier: MIT
// https://etherscan.io/address/0xcbe6b83e77cdc011cc18f6f0df8444e5783ed982#code
pragma solidity 0.8.9;

import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/utils/cryptography/MerkleProof.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "./UnionBase.sol";

// Allows anyone to claim a token if they exist in a merkle root.
contract MerkleDistributor is ReentrancyGuard, UnionBase {
    using SafeERC20 for IERC20;

    // Possible options when claiming
    enum Option {
        Claim,
        ClaimAsETH,
        ClaimAsCRV,
        ClaimAsCVX,
        ClaimAndStake
    }

    address public immutable token;
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
        uint256 week,
        Option indexed option
    );
    // This event is triggered whenever the merkle root gets updated.
    event MerkleRootUpdated(bytes32 indexed merkleRoot, uint32 indexed week);
    // This event is triggered whenever the admin is updated.
    event AdminUpdated(address indexed oldAdmin, address indexed newAdmin);

    constructor(address token_, address depositor_, bytes32 merkleRoot_) {
        token = token_;
        admin = msg.sender;
        depositor = depositor_;
        merkleRoot = merkleRoot_;
        week = 0;
        frozen = true;
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

    /// @notice Set approvals for the tokens used when swapping
    function setApprovals() external onlyAdmin {
        IERC20(CRV_TOKEN).safeApprove(CURVE_TRICRV_POOL, 0);
        IERC20(CRV_TOKEN).safeApprove(CURVE_TRICRV_POOL, 2 ** 256 - 1);

        IERC20(CVXCRV_TOKEN).safeApprove(CVXCRV_STAKING_CONTRACT, 0);
        IERC20(CVXCRV_TOKEN).safeApprove(CVXCRV_STAKING_CONTRACT, 2 ** 256 - 1);

        IERC20(CVXCRV_TOKEN).safeApprove(CURVE_CVXCRV_CRV_POOL, 0);
        IERC20(CVXCRV_TOKEN).safeApprove(CURVE_CVXCRV_CRV_POOL, 2 ** 256 - 1);
    }

    /// @notice Transfers ownership of the contract
    /// @param newAdmin - address of the new admin of the contract
    function updateAdmin(address newAdmin) external onlyAdmin {
        require(newAdmin != address(0));
        address oldAdmin = admin;
        admin = newAdmin;
        emit AdminUpdated(oldAdmin, newAdmin);
    }

    /// @notice Claim the given amount of the token to the given address.
    /// Reverts if the inputs are invalid.
    /// @param index - claimer index
    /// @param account - claimer account
    /// @param amount - claim amount
    /// @param merkleProof - merkle proof for the claim
    /// @param option - claiming option
    function claim(
        uint256 index,
        address account,
        uint256 amount,
        bytes32[] calldata merkleProof,
        Option option
    ) external nonReentrant {
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

        if (option == Option.ClaimAsCRV) {
            _swapCvxCrvToCrv(amount, account);
        } else if (option == Option.ClaimAsETH) {
            uint256 _crvBalance = _swapCvxCrvToCrv(amount, address(this));
            uint256 _ethAmount = _swapCrvToEth(_crvBalance);
            (bool success, ) = account.call{value: _ethAmount}("");
            require(success, "ETH transfer failed");
        } else if (option == Option.ClaimAsCVX) {
            uint256 _crvBalance = _swapCvxCrvToCrv(amount, address(this));
            uint256 _ethAmount = _swapCrvToEth(_crvBalance);
            uint256 _cvxAmount = _swapEthToCvx(_ethAmount);
            IERC20(CVX_TOKEN).safeTransfer(account, _cvxAmount);
        } else if (option == Option.ClaimAndStake) {
            require(cvxCrvStaking.stakeFor(account, amount), "Staking failed");
        } else {
            IERC20(token).safeTransfer(account, amount);
        }

        emit Claimed(index, amount, account, week, option);
    }

    /// @notice Freezes the claim function to allow the merkleRoot to be changed
    /// @dev Can be called by the owner or the depositor zap contract
    function freeze() public {
        require(
            (msg.sender == admin) || (msg.sender == depositor),
            "Admin or depositor only"
        );
        frozen = true;
    }

    /// @notice Unfreezes the claim function.
    function unfreeze() public onlyAdmin {
        frozen = false;
    }

    /// @notice Update the merkle root and increment the week.
    /// @param _merkleRoot - the new root to push
    function updateMerkleRoot(bytes32 _merkleRoot) public onlyAdmin {
        require(frozen, "Contract not frozen.");

        // Increment the week (simulates the clearing of the claimedBitMap)
        week = week + 1;
        // Set the new merkle root
        merkleRoot = _merkleRoot;

        emit MerkleRootUpdated(merkleRoot, week);
    }

    receive() external payable {}

    modifier onlyAdmin() {
        require(msg.sender == admin, "Admin only");
        _;
    }
}
