from brownie import accounts, interface, EPSClaim

ZAP_V3 = "0x83507cc8C8B67Ed48BADD1F59F684D5d02884C81"
EPS = "0xa7f552078dcc247c2684336020c03648500c6d9f"
# distributions:
# https://github.com/ellipsis-finance/vecrv-airdrop/tree/master/distributions

amount1 = 57784323459245420000
amount2 = 1189699047100317071873
claim1 = ["0x7eb841876ca7b41e5c5b9e40718214e9bf8c8186",
          ZAP_V3,
          amount1,
          [
              "0x151da19b83d5e9f07968a778cc4d123d10daf2dfb4e2d9d141ca1c8902f056b5",
              "0x9f446022588ae244a12011a84e179953a110ec2b7d82f5849a67ca64c2b49ac6",
              "0x622e85fdf203c4f75603e4854c717a08f8bec411b4e63e07f05075a3771b1a5d",
              "0xa39da9b8c5715e10f3a1b67c4b106ff53516258a1f5d2e5406655fe390790026",
              "0x091131c2ae137e21a972e6feada3d5c6413a8107884dec4b7b3d4e2f82ba8ad8",
              "0x216d511bd1861a1b9af82fdf36e9c6fe2146155b9d98946e682c27e0c5a7cd27",
              "0x427262a7a71fc7af04f28644f9f9b472b42d71894345a8d433668d90b1bb2da2",
              "0x1c44e5f13e78b787033c4002e93f6e010a53ec5d5b8588ca0755fe8f5c884682",
              "0xcb3e8308ba48eb7f4e600bba113ecea20d746566e640f611a984dbea4238af94",
              "0x5dd14a7eb6029b1789976c9fc39ee2eecd3024da3eb856aa3d5096bf16f655f1",
              "0x33fcfce8f46dfda26422b2adea17ed3ddd528f8fda814621886400077311f092",
              "0x5ea8e7f64e86f0574ebe83128aaad011c917ac2c2e667ece3877c60082ac9c69",
              "0x0797f5593da7d3f6fbe8265429e2e6df6d79a751401a99b8c8bb2b217afb0ccc",
              "0x72ce5c94538378d10f040f10d46d32f2cab1fcf6bf9304ab47e6dad7024c3dfe"
          ]
          ]

claim2 = ["0xf776ad79740115b826ec4bcf3641329852625399",
          ZAP_V3,
          amount2,
          [
              "0x77099ac5d97b8664904b077e545ab5f47a1cb187c926215b1d6c8aba5b083947",
              "0xf2df56d4fd81b2425097a52a8931084fe44ebba5565a8aa60a5e4442f0e19709",
              "0x0b1ae779808d9607466e73bef17a83352e31346841d5c9be071219c944b5eb93",
              "0xd1e486c316ee499e8275edb2fad572709e9cc310bf092c9cbcf504544acc2c47",
              "0xeba0b90debe6a2c95c03b877907a0a0ace1d3cf0354e8e24d49054dfc2dc91be",
              "0xe10f1cc93028c3af70ded3e41b84220ba4f230ccc172f4549a0f49d67d64900d",
              "0x329fd09c9e6926284c8cede8c44663a0817951f85e835d8655f664854dc0693a",
              "0xd20f14bfdc0e13d2b6fdcd287e409e466e07c6bc1e383dadc16a16e4f9e12a7c",
              "0x1136791130786bb15870154ccb415d6128c142290c72622dfd5c817c2e19f0a4",
              "0x9b1de31e2c8c9253d01e8621788006d15a49d58fe3803f3d010ab80c25846001",
              "0x39e67424dfa5c9d5beffa91ee645958224ba4410fa757d863e69b572681e70b9",
              "0x1688e6f3ed72c2458c69685182f32d04c99f34750895f977a3f359a7cee5835b",
              "0xf60e2da51f6af0d0c4667a4fda7c9383640bfda9cb2dac17f0c9b0313775e6f7",
              "0xe2286410138877bf45af81f7f40e6c0bc7d11957684580bbb5e605ebcfafb75c"
          ]
          ]


def main():
    deployer = accounts.load("mainnet-deploy")

    # up the nonce to 18
    for i in range(17):
        deployer.transfer(deployer, 1)

    eps = EPSClaim.deploy({'from': deployer})
    assert eps.address == ZAP_V3
    eps.claim([claim1, claim2], deployer.address, {'from': deployer})
    assert interface.IERC20(EPS).balanceOf(deployer) == amount1 + amount2

