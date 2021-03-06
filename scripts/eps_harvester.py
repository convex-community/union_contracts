from brownie import accounts, interface, EPSClaim
import requests

CVXCRV_VAULT = "0x83507cc8C8B67Ed48BADD1F59F684D5d02884C81"
EPS = "0xa7f552078dcc247c2684336020c03648500c6d9f"

CVX_EPS_AIRDROP_ENDPOINT = (
    f"https://www.convexfinance.com/api/eps/address-airdrop-info?address={CVXCRV_VAULT}"
)
r = requests.get(CVX_EPS_AIRDROP_ENDPOINT)
proofs = r.json()["matchedAirdropData"]

contracts = [
    "0x5F863EDFB62575fe3A838C2afB4919dEd7b511D9",
    "0x48389D205Ae9B345C34B1048407fEfa848DfC06F",
    "0x43144b4Fc9539DEe891127B8A608d2090C92caa7",
    "0x23377628Cb549cbfeb9138d4aE70751cF67C44F4",
    "0xE09ebF1Cb830D6c334b7Ab973e04Ba2d84B77043",
    "0x58e330559998e93De19032066be8DbAB3E1e8c4a",
    "0xf140b370Ae1238Add424d3F9B7ED409dAdB7E238",
    "0x81E47381aA927ffA2138263e50716B1C573B0Eb5",
    "0xc789F8fc2dD7D14DFFEA9e3D7e78BDe43ea9F439",
    "0xA0f7B26ccDc490ef9E5CedB7e956351aA4bE5B1B",
    "0xcbCa4Cd79aF621184DDc14CDC6C43E37Db780470",
    "0xA988E0B94F0b187474ff45D7ca9F1ecbe80824E7",
    "0x4BF0172272470125486CEaD15718f9B7B5185E02",
    "0x37a0f7cac3b4AaDFc4347cCd4c890604AC3DAfDa",
    "0x3d7F3140aCc4176cf510008A5773a7Be7cDe0fBA",
    "0x0d59D439a4466Ef2b22d50d11eABcCbd54f42052",
    "0x37E18aaB177E169dAA33D24F26b8ab3A6ccf0c0e",
    "0x1639f30b195d25b254Cc128Ac9d864707D30Df00",
    "0xfb0e623295C0599DECAf1d40046D728D6e7a58E9",
    "0xF76Ab4382d3737e6199812fbDDAF459e250EcEdc",
    "0xE8aA47084509f1927946354a079279644Ba6fb1F",
    "0x79b89544C3f6cba5e780814c40d7F669CB7fb20D",
    "0x565F9554b47Db0772c754fa7A04507aa3b50122E",
    "0x0Be356523A96D477bc5d7768475f22B56798aDca",
    "0xF918f28e1E83151c30C9bD99b0B55362754D616C",
    "0x6e4fA069a6aAbd2529838dEbeD2435e9eAcc1A00",
    "0xAcf27590F75d8eA23DEc61AE8F23BC75E9De6fFB",
    "0x6F5741E32570faa767301bB5FB7d892FAd75a12f",
    "0xAfeb9F72C451c581EA75613C38F4F3d4B29C92c8",
    "0xf0708696f86d08287e5C1A525E38592D8456676e",
    "0x03cbDC39a41b0D8d192BaC8E2f92c73Feacc938E",
    "0xCC093A6E8082aDf38Bb70D9b0aC761c666ff03F4",
    "0xEa6672757f5D11237EAAf978Da09eC619Ff4e63F",
    "0x337465264408D0289F9fE4B39277cE62CECa3E01",
    "0x7eB841876ca7b41e5c5b9E40718214e9Bf8c8186",
    "0xF776ad79740115B826Ec4BcF3641329852625399",
    "0x15418C448AE061e8765f4936e2df73C2852BF5e4",
    "0xa0f8aeD5E5274D03114880bae562828314dE149d",
    "0x16c0b34Dcee8a57A068500c5364A323B41Bd05cB",
    "0xDAB55C39784b24C68C20b54f3f14494E208BA215",
    "0xC850B3F0737B59C47Be7E3b3439C45567A0E95fB",
    "0x158F8f5B1cCb172bb79EAb75ED11eE70083f0e12",
    "0x3EE776BE4Eb9Ac0a7D2DF18052d33fD13abaA476",
    "0xfB5b140b85EC3a05b2E934dbABEc2c9251A3CEaf",
]


def main():
    deployer = accounts.load("mainnet-deploy")

    # up the nonce to 18
    for i in range(17):
        deployer.transfer(deployer, 1)

    eps = EPSClaim.deploy({"from": deployer})
    assert eps.address == CVXCRV_VAULT
    claims = []
    total_amount = 0
    for i, proof in enumerate(proofs):
        if proof is None:
            continue
        current_claim = [
            contracts[i],
            CVXCRV_VAULT,
            int(proof["amount"]),
            proof["proof"],
        ]
        claims.append(current_claim)
        total_amount += int(proof["amount"])
    print(f"Claiming: {total_amount} EPS ({len(claims)} claims)")
    eps.claim(claims, deployer.address, {"from": deployer})
    assert interface.IERC20(EPS).balanceOf(deployer) == total_amount
