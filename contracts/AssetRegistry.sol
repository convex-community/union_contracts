// SPDX-License-Identifier: MIT
pragma solidity 0.8.9;


contract AssetRegistry {
    // assetChoices records the proportions of different output assets
    // that a Union member would like to split their bribes between.
    // There is a maximum of 16 available assets, although not all may be
    // used. Any uint16 can be used to express the weights, which are
    // meant to be normalized afterwards.
    // So weights of [2, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    // and [50, 25, 0, 25, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    // would be equivalent.
    mapping(address => uint16[16]) public assetChoices;

    function recordPreferences(uint32[16] calldata choices) external {
        assetChoices[msg.sender] = choices;
    }

}
