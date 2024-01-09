# @version 0.3.9
"""
@title Both zap auraBal harvest to ETH
@license MIT
"""

struct SingleSwap:
    pool_id: bytes32
    kind: uint8
    asset_in: address
    asset_out: address
    amount: uint256
    user_data: Bytes[32]

struct FundManagement:
    sender: address 
    from_internal_balance: bool
    recipient: address
    to_internal_balance: bool

struct ExitPoolRequest:
    assets: DynArray[address, 2]
    min_amounts_out: DynArray[uint256, 2]
    user_data: Bytes[96]
    to_internal_balance: bool

interface UnionVault:
    def harvest(_min_amount_out: uint256, _lock: bool): nonpayable

interface ERC20:
    def balanceOf(_addr: address) -> uint256: view
    def approve(spender: address, amount: uint256) -> bool: nonpayable

interface BalVault:
    def swap(single_swap: SingleSwap, funds: FundManagement, limit: uint256, deadline: uint256) -> uint256: payable
    def exitPool(pool_id: bytes32, sender: address, recipient: address, request: ExitPoolRequest): nonpayable

authorized_callers: public(HashMap[address, bool])
owner: public(address)

# ---- storage variables ---- #
aurabal_pounder: immutable(address)

# --- constants --- #
AURABAL_TOKEN: constant(address) = 0x616e8BfA43F920657B3497DBf40D6b1A02D4608d
BAL_TOKEN: constant(address)= 0xba100000625a3754423978a60c9317c58a424e3D
BAL_VAULT: constant(address) = 0xBA12222222228d8Ba445958a75a0704d566BF2C8
AURABAL_BAL_ETH_BPT_POOL_ID: constant(bytes32) = 0x3dd0843a028c86e0b760b1a76929d1c5ef93a2dd000200000000000000000249
BAL_ETH_POOL_TOKEN: constant(address) = 0x5c6Ee304399DBdB9C8Ef030aB642B10820DB8F56
BAL_ETH_POOL_ID: constant(bytes32) = 0x5c6ee304399dbdb9c8ef030ab642b10820db8f56000200000000000000000014
GIVEN_IN: constant(uint8) = 0
EXACT_BPT_IN_FOR_ONE_TOKEN_OUT: constant(uint8) = 0


@external
def __init__(
        _aurabal_pounder: address
):
    aurabal_pounder = _aurabal_pounder
    self.owner = msg.sender
    self.authorized_callers[msg.sender] = True

@external
def change_owner(_owner: address):
    assert(msg.sender == self.owner)
    self.owner = _owner

@external
def set_approvals():
    ERC20(BAL_ETH_POOL_TOKEN).approve(BAL_VAULT, 0)
    ERC20(BAL_ETH_POOL_TOKEN).approve(BAL_VAULT, MAX_UINT256)
    ERC20(AURABAL_TOKEN).approve(BAL_VAULT, 0)
    ERC20(AURABAL_TOKEN).approve(BAL_VAULT, MAX_UINT256)

@external
def update_authorized_caller(_caller: address, _authorized: bool):
    assert(msg.sender == self.owner)
    self.authorized_callers[_caller] = _authorized

@internal
def _createSwapFunds() -> FundManagement:
    return FundManagement({sender: self,
    from_internal_balance: False,
    recipient: self,
    to_internal_balance: False})

@external
def harvest(_min_amount_out: uint256, _lock: bool) -> uint256:
    assert(self.authorized_callers[msg.sender])
    original_balance: uint256 = msg.sender.balance
    UnionVault(aurabal_pounder).harvest(_min_amount_out, _lock)
    auraBalBalance: uint256 = ERC20(AURABAL_TOKEN).balanceOf(self)
    auraBalParams: SingleSwap = SingleSwap({
        pool_id: AURABAL_BAL_ETH_BPT_POOL_ID,
        kind: GIVEN_IN,
        asset_in: AURABAL_TOKEN,
        asset_out: BAL_ETH_POOL_TOKEN,
        amount: auraBalBalance,
        user_data: empty(Bytes[32])
    })
    bpt_balance: uint256 = BalVault(BAL_VAULT).swap(
                auraBalParams,
                self._createSwapFunds(),
                0,
                block.timestamp + 1
            )
    exit_assets: DynArray[address, 2] = [BAL_TOKEN, empty(address)]
    min_outs: DynArray[uint256, 2] = [0, _min_amount_out]
    asset_index: uint256 = 1
    exit_request: ExitPoolRequest = ExitPoolRequest({
            assets: exit_assets,
            min_amounts_out: min_outs,
            user_data: _abi_encode(EXACT_BPT_IN_FOR_ONE_TOKEN_OUT,
            bpt_balance,
            asset_index),
            to_internal_balance: False
        })

    BalVault(BAL_VAULT).exitPool(
        BAL_ETH_POOL_ID,
        self,
        msg.sender,
        exit_request
    )
    return (msg.sender.balance - original_balance)
    

@external
@payable
def __default__():
    pass