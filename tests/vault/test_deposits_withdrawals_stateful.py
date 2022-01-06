import brownie
from brownie.test import strategy
from brownie import chain, Contract, interface

from ..utils import approx
from ..utils.constants import CVXCRV_REWARDS, CVXCRV, CURVE_CVXCRV_CRV_POOL

DAY = 86400


class StateMachine:

    value = strategy("uint256", min_value=1000000, max_value="1000 ether")
    days = strategy("uint256", min_value=1, max_value=10)
    address = strategy("address", length=9)

    def __init__(self, accounts, vault):
        self.accounts = accounts
        self.vault = vault
        self.cvxcrv = interface.IERC20(CVXCRV)
        self.callIncentive = self.vault.callIncentive()
        self.platformFee = self.vault.platformFee()
        self.platform = self.vault.platform()
        self.withdrawalPenalty = self.vault.withdrawalPenalty()

    def setup(self):
        self.share_balances = {i: 0 for i in self.accounts}
        for account in self.accounts:
            self.vault.deposit(account, 1e20, {"from": account})

    def rule_deposit(self, address, value):
        original_address_balance = self.cvxcrv.balanceOf(address)
        original_address_vault_balance = self.vault.balanceOf(address)
        if original_address_balance < value:
            return
        prior_vault_balance = self.vault.totalHoldings()
        prior_supply = self.vault.totalSupply()
        self.vault.deposit(address, value, {"from": address})
        assert self.vault.totalHoldings() == prior_vault_balance + value
        assert self.cvxcrv.balanceOf(address) == original_address_balance - value
        assert self.vault.balanceOf(address) == original_address_vault_balance + (
            (value * prior_supply) // prior_vault_balance
        )

    def rule_let_yield_accumulate(self):
        chain.sleep(DAY * 10)

    def rule_harvest(self):
        original_address_balance = self.cvxcrv.balanceOf(self.accounts[0])
        prior_vault_balance = self.vault.totalHoldings()
        platform_initial_balance = self.cvxcrv.balanceOf(self.platform)
        tx = self.vault.harvest({"from": self.accounts[0]})
        harvested_amount = tx.events["Harvest"]["amount"]
        platform_fees = harvested_amount * self.platformFee // 10000
        caller_incentive = harvested_amount * self.callIncentive // 10000
        assert self.vault.totalHoldings() >= prior_vault_balance
        assert approx(
            (self.cvxcrv.balanceOf(self.accounts[0]) - original_address_balance),
            caller_incentive,
            1e-5,
        )
        assert approx(
            self.cvxcrv.balanceOf(self.platform),
            platform_initial_balance + platform_fees,
            1e-5,
        )

    def rule_withdraw(self, address):
        shares = self.vault.balanceOf(address)
        non_withdrawers = [
            account for account in self.accounts if account.address != address
        ]
        claimable_non_withdrawer = self.vault.balanceOfUnderlying(non_withdrawers[0])
        original_balance = self.cvxcrv.balanceOf(address)
        claimable = self.vault.balanceOfUnderlying(address)
        to_withdraw = shares // 4
        expected_gross_withdrawn = claimable // 4
        if to_withdraw == 0:
            return
        self.vault.withdraw(address, to_withdraw, {"from": address})
        penalty_amount = expected_gross_withdrawn * self.withdrawalPenalty // 10000
        claimed = self.cvxcrv.balanceOf(address) - original_balance
        assert approx(claimed, expected_gross_withdrawn - penalty_amount, 1e-3)
        assert (
            self.vault.balanceOfUnderlying(non_withdrawers[0])
            > claimable_non_withdrawer
        )

    def teardown_final(self):
        for i, account in enumerate(self.accounts):
            shares = self.vault.balanceOf(account)
            if shares == 0:
                continue
            claimable = shares * self.vault.totalHoldings() // self.vault.totalSupply()
            fee = claimable * self.vault.withdrawalPenalty() // 10000
            prior_cvxcrv_balance = self.cvxcrv.balanceOf(account)
            self.vault.withdrawAll(account, {"from": account})
            withdrawn = self.cvxcrv.balanceOf(account) - prior_cvxcrv_balance
            if i != len(self.accounts) - 1:
                assert approx(withdrawn, claimable - fee, 1e-2)

        assert self.vault.totalSupply() == 0
        assert self.vault.totalHoldings() == 0


def test_vault_deposit_withdraw(state_machine, accounts, UnionVault):
    owner = accounts[0]
    chain.snapshot()
    vault = UnionVault.deploy({"from": owner})
    vault.setApprovals({"from": owner})
    for account in accounts[:10]:
        interface.IERC20(CVXCRV).transfer(
            account.address, 2e22, {"from": CURVE_CVXCRV_CRV_POOL}
        )

        interface.IERC20(CVXCRV).approve(vault, 2 ** 256 - 1, {"from": account})

    state_machine(
        StateMachine,
        accounts[:10],
        vault,
        settings={"max_examples": 50},
    )
    chain.revert()
