// SPDX-License-Identifier: UNLICENSED
pragma solidity 0.8.9;

interface IStakingRewards {
    function stakeFor(address, uint256) external returns (bool);

    function balanceOf(address) external view returns (uint256);

    function earned(address) external view returns (uint256);

    function withdrawAll(bool) external returns (bool);

    function withdraw(uint256, bool) external returns (bool);

    function withdrawAndUnwrap(uint256 amount, bool claim)
        external
        returns (bool);

    function getReward() external returns (bool);

    function stake(uint256) external returns (bool);

    function extraRewards(uint256) external view returns (address);

    function exit() external returns (bool);

    function setDistributor(address _distributor) external;

    function setRewardsDuration(uint256 _rewardsDuration) external;

    function recoverERC20(address tokenAddress, uint256 tokenAmount) external;

    function notifyRewardAmount(uint256 reward) external;
}
