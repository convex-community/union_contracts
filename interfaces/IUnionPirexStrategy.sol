// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

interface IUnionPirexStrategy {
    function redeemRewards(uint256 epoch, uint256[] calldata rewardIndexes)
        external;

    function totalSupply() external view returns (uint256);

    function totalSupplyWithRewards() external view returns (uint256, uint256);

    function lastTimeRewardApplicable() external view returns (uint256);

    function rewardPerToken() external view returns (uint256);

    function earned() external view returns (uint256);

    function getRewardForDuration() external view returns (uint256);

    function stake(uint256 amount) external;

    function withdraw(uint256 amount) external;

    function getReward() external;

    function notifyRewardAmount() external;

    function recoverERC20(address tokenAddress, uint256 tokenAmount) external;

    function setDistributor(address _distributor) external;
}
