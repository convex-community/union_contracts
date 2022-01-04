// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

interface IUnionVault {
    enum Option {
        Claim,
        ClaimAsETH,
        ClaimAsCRV,
        ClaimAsCVX,
        ClaimAndStake
    }

    function withdraw(uint256 _shares) external returns (uint256 withdrawn);

    function withdrawAll() external returns (uint256 withdrawn);

    function withdrawAs(uint256 _shares, Option option) external;

    function withdrawAllAs(Option option) external;

    function depositAll() external;

    function deposit(uint256 _amount) external;

    function harvest() external;

    function claimable(address user) external view returns (uint256 amount);

    function outstanding3CrvRewards() external view returns (uint256 total);

    function outstandingCvxRewards() external view returns (uint256 total);

    function outstandingCrvRewards() external view returns (uint256 total);

    function stakeBalance() external view returns (uint256 total);

    function setPlatform(address _platform) external;

    function setPlatformFee(uint256 _fee) external;

    function setCallIncentive(uint256 _incentive) external;

    function setWithdrawalPenalty(uint256 _penalty) external;

    function setApprovals() external;
}
