from tabulate import tabulate

from tests.utils.cvxfxs import eth_to_fxs

REDC = "\033[93m"
ENDC = "\033[0m"

def main():
    amounts = [1e17, 1e18, 1e19, 1e20]
    options = [0,1,2,3]
    headers = ["Route", "Amount In", "Amount Out"]
    report = []
    for amount in amounts:
        amounts_out = []
        for option in options:
            amounts_out.append(int(eth_to_fxs(amount, option))  * 1e-18)
        for i, option in enumerate(options):
            out = REDC + str(amounts_out[i]) + ENDC if amounts_out[i] == max(amounts_out) else str(amounts_out[i])
            report.append([
                option,
                int(amount) * 1e-18,
                out
            ])

    print(tabulate(report, headers=headers))
