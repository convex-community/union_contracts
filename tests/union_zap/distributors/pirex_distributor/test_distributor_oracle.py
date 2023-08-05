from brownie import interface, chain

from tests.utils import CVX, approx
from tests.utils.constants import (
    LPXCVX_POOL,
    CVX_STAKING_CONTRACT,
    PXCVX_TOKEN,
    LPXCVX_TOKEN,
    PIREX_CVX_STRATEGY,
)


def test_distribution_no_discount(fn_isolation, cvx_distributor, cvx_vault, owner):
    cvx = interface.IERC20(CVX)
    lpcvx_swap = interface.ICurveV2Pool(LPXCVX_POOL)
    cvx.approve(LPXCVX_POOL, 2**256 - 1, {"from": CVX_STAKING_CONTRACT})
    print(f"Price oracle before {lpcvx_swap.price_oracle() * 1e-18}")
    total_liq = int(1e24)  # int(cvx.balanceOf(CVX_STAKING_CONTRACT) * 0.75)
    steps = 5
    for i in range(steps):
        lpcvx_swap.add_liquidity(
            [total_liq // steps, 0],
            0,
            {"from": CVX_STAKING_CONTRACT},
        )
        chain.sleep(10000)
        chain.mine(1)
    print(f"Price oracle after {lpcvx_swap.price_oracle() * 1e-18}")

    distributor_original_balance = cvx_vault.maxWithdraw(cvx_distributor)

    amount = 1e21
    interface.IERC20(CVX).transfer(
        cvx_distributor, amount, {"from": CVX_STAKING_CONTRACT}
    )
    cvx_distributor.stake({"from": owner})

    assert approx(
        cvx_vault.maxWithdraw(cvx_distributor),
        distributor_original_balance + amount,
        1e-5,
    )


def test_distribution_with_discount(fn_isolation, cvx_distributor, cvx_vault, owner):
    pxcvx = interface.IERC20(PXCVX_TOKEN)
    lpcvx = interface.IERC20(LPXCVX_TOKEN)
    total_liq = int(1e24)

    pxcvx.approve(LPXCVX_TOKEN, 2**256 - 1, {"from": PIREX_CVX_STRATEGY})
    interface.ILpxCvx(LPXCVX_TOKEN).wrap(total_liq, {"from": PIREX_CVX_STRATEGY})

    lpcvx_swap = interface.ICurveV2Pool(LPXCVX_POOL)
    lpcvx.approve(LPXCVX_POOL, 2**256 - 1, {"from": PIREX_CVX_STRATEGY})
    print(f"Price oracle before {lpcvx_swap.price_oracle() * 1e-18}")

    steps = 5
    for i in range(steps):
        lpcvx_swap.add_liquidity(
            [0, total_liq // steps],
            0,
            {"from": PIREX_CVX_STRATEGY},
        )
        chain.sleep(10000)
        chain.mine(1)
    print(f"Price oracle after {lpcvx_swap.price_oracle() * 1e-18}")

    distributor_original_balance = cvx_vault.maxWithdraw(cvx_distributor)

    amount = 1e21
    interface.IERC20(CVX).transfer(
        cvx_distributor, amount, {"from": CVX_STAKING_CONTRACT}
    )
    cvx_distributor.stake({"from": owner})

    assert (
        cvx_vault.maxWithdraw(cvx_distributor) > distributor_original_balance + amount
    )
