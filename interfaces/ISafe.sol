// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;

interface ISafe {
    function nonce() external view returns (uint256);

    function isOwner(address owner) external view returns (bool);

    function getTransactionHash(
        address to,
        uint256 value,
        bytes calldata data,
        uint8 operation,
        uint256 safeTxGas,
        uint256 baseGas,
        uint256 gasPrice,
        address gasToken,
        address refundReceiver,
        uint256 nonce
    ) external view returns (bytes32);
}
