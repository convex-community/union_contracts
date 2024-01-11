// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

import "../../GenericVault.sol";

error ZeroAddress();

interface IstkCvxPrismaStrategy {
    function harvest(address _caller, uint256 _minAmountOut)
        external
        returns (uint256 harvested);
}

interface ICvxPrismaStaking {
    function claimableRewards(address _account)
        external
        view
        returns (EarnedData[] memory userRewards);

    struct EarnedData {
        address token;
        uint256 amount;
    }
}

contract stkCvxPrismaVault is GenericUnionVault {
    bool public isHarvestPermissioned;
    mapping(address => bool) public authorizedHarvesters;
    ICvxPrismaStaking constant cvxPrismaStaking =
        ICvxPrismaStaking(0x0c73f1cFd5C9dFc150C8707Aa47Acbd14F0BE108);

    constructor(address _token) GenericUnionVault(_token) {}

    /// @notice Sets whether only whitelisted addresses can harvest
    /// @param _status Whether or not harvests are permissioned
    function setHarvestPermissions(bool _status) external onlyOwner {
        isHarvestPermissioned = _status;
    }

    /// @notice Adds or remove an address from the harvesters' whitelist
    /// @param _harvester address of the authorized harvester
    /// @param _authorized Whether to add or remove harvester
    function updateAuthorizedHarvesters(address _harvester, bool _authorized)
        external
        onlyOwner
    {
        if (_harvester == address(0)) revert ZeroAddress();
        authorizedHarvesters[_harvester] = _authorized;
    }

    /// @notice Claim rewards and swaps them to cvxPrisma for restaking
    /// @param _minAmountOut - min amount of cvxPrisma to receive for harvest
    /// @dev Can be called by whitelisted account or anyone against a cvxPrisma incentive
    /// @dev Harvest logic in the strategy/harvester contract
    /// @dev Harvest can be called even if permissioned when last staker is
    ///      withdrawing from the vault.
    function harvest(uint256 _minAmountOut) public {
        require(
            !isHarvestPermissioned ||
                authorizedHarvesters[msg.sender] ||
                totalSupply() == 0,
            "permissioned harvest"
        );
        uint256 _harvested = IstkCvxPrismaStrategy(strategy).harvest(
            msg.sender,
            _minAmountOut
        );
        emit Harvest(msg.sender, _harvested);
    }

    /// @notice View function to get pending staking rewards
    function claimableRewards()
        external
        view
        returns (ICvxPrismaStaking.EarnedData[] memory)
    {
        return cvxPrismaStaking.claimableRewards(strategy);
    }

    /// @notice Claim rewards and swaps them to cvxPrisma for restaking
    /// @dev No slippage protection (harvester will use oracles)
    function harvest() public override {
        harvest(0);
    }
}
