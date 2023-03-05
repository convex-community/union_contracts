// SPDX-License-Identifier: UNLICENSED
pragma solidity 0.8.9;

interface ICvxFxsStaking {
    function balanceOf(address) external view returns (uint256);

    function withdraw(uint256) external;

    function getReward() external returns (bool);

    function stake(uint256) external;

    function stakeFor(address, uint256) external returns (bool);

    function stakeAll() external returns (bool);

    function addReward(address _rewardsToken, address _distributor) external;

    function approveRewardDistributor(
        address _rewardsToken,
        address _distributor,
        bool _approved
    ) external;

    function notifyRewardAmount(address _rewardsToken, uint256 _reward)
        external;
}
