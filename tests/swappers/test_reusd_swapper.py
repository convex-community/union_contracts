import pytest
from brownie import ReUsdSwapper, interface


@pytest.fixture(scope="module")
def depositor(module_isolation, accounts):
    # Common dev accounts can have EIP-7702 delegations on mainnet forks.
    depositor = accounts.add()
    accounts[0].transfer(depositor, 10**18)
    return depositor


@pytest.fixture(scope="module")
def swapper(accounts, depositor):
    swapper = ReUsdSwapper.deploy(depositor, {"from": accounts[0]})
    swapper.setApprovals({"from": accounts[0]})
    return swapper


@pytest.fixture(scope="module")
def pools(swapper):
    return (
        interface.ICurveTriCryptoFactoryNG(swapper.TRICRV_POOL()),
        interface.ICurveStableSwapNG(swapper.REUSD_POOL()),
        interface.IERC4626(swapper.SCRVUSD_VAULT()),
    )


def test_price_matches_executable_sell_quote(swapper, pools):
    tri_pool, reusd_pool, vault = pools
    amount = 100 * 10**18
    shares = reusd_pool.get_dy(0, 1, amount)
    assets = vault.previewRedeem(shares)
    quote = tri_pool.get_dy(0, 1, assets)
    valuation = amount * swapper.price_oracle() // 10**18

    # Independent market quote: the old adapter overvalued this by about 13%.
    assert abs(valuation - quote) * 10_000 <= quote * 100


@pytest.mark.parametrize("amount", [10**15, 10**17])
def test_buy_with_oracle_protection(swapper, pools, depositor, amount):
    tri_pool, reusd_pool, vault = pools
    reusd = interface.IERC20(swapper.REUSD_TOKEN())
    assets = tri_pool.get_dy(1, 0, amount)
    quote = reusd_pool.get_dy(1, 0, vault.previewDeposit(assets))
    balance_before = reusd.balanceOf(depositor)

    depositor.transfer(swapper, amount)
    tx = swapper.buy(amount, {"from": depositor})

    assert reusd.balanceOf(depositor) - balance_before == tx.return_value
    assert abs(tx.return_value - quote) * 10_000 <= quote * 100
    pool_call = next(
        call
        for call in tx.subcalls
        if call["to"] == reusd_pool.address and call["op"] == "CALL"
    )
    _, inputs = interface.ICurveStableSwapNG.decode_input(pool_call["calldata"])
    minimum = inputs[3]
    # A 3% oracle limit must remain close to the independent market quote.
    # The old buy formula allowed roughly 14% slippage at the regression block.
    assert quote * 96 // 100 <= minimum <= quote * 98 // 100


@pytest.mark.parametrize("amount", [10**15, 10**17])
def test_sell_with_oracle_protection(swapper, pools, depositor, amount):
    tri_pool, reusd_pool, vault = pools
    reusd = interface.IERC20(swapper.REUSD_TOKEN())
    depositor.transfer(swapper, amount)
    bought = swapper.buy(amount, {"from": depositor}).return_value
    shares = reusd_pool.get_dy(0, 1, bought)
    quote = tri_pool.get_dy(0, 1, vault.previewRedeem(shares))

    reusd.transfer(swapper, bought, {"from": depositor})
    balance_before = depositor.balance()
    tx = swapper.sell(bought, {"from": depositor})

    assert (
        depositor.balance() + tx.gas_used * tx.gas_price
        == balance_before + tx.return_value
    )
    assert abs(tx.return_value - quote) * 10_000 <= quote * 100
    assert reusd.balanceOf(swapper) == 0
