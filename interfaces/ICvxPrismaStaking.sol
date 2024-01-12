// SPDX-License-Identifier: UNLICENSED
pragma solidity 0.8.9;

interface ICvxPrismaStaking {
    function balanceOf(address) external view returns (uint256);

    function withdraw(uint256) external;

    function getReward(address _address) external;

    function getReward(address _address, address _forwardTo) external;

    function stake(uint256) external;

    function stakeFor(address, uint256) external;

    function stakeAll() external;

    function addReward(address _rewardsToken, address _distributor) external;

    function approveRewardDistributor(
        address _rewardsToken,
        address _distributor,
        bool _approved
    ) external;

    function setRewardRedirect(address _to) external;

    function notifyRewardAmount(address _rewardsToken, uint256 _reward)
        external;
}
