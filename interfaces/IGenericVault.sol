// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

interface IGenericVault {
    function withdraw(address _to, uint256 _shares)
    external
    returns (uint256 withdrawn);

    function withdrawAll(address _to) external returns (uint256 withdrawn);

    function depositAll(address _to) external returns (uint256 _shares);

    function deposit(address _to, uint256 _amount)
    external
    returns (uint256 _shares);

    function harvest() external;

    function balanceOfUnderlying(address user)
    external
    view
    returns (uint256 amount);

    function totalUnderlying() external view returns (uint256 total);

    function totalSupply() external view returns (uint256 total);

    function underlying() external view returns (address);

    function setPlatform(address _platform) external;

    function setPlatformFee(uint256 _fee) external;

    function setCallIncentive(uint256 _incentive) external;

    function setWithdrawalPenalty(uint256 _penalty) external;

    function setApprovals() external;
}