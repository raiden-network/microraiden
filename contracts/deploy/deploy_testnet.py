"""
A simple Python script to deploy contracts and then do a smoke test for them.
"""
from populus import Project
from populus.utils.wait import wait_for_transaction_receipt
from web3 import Web3
from web3.utils.compat import (
    Timeout,
)
senders = [
    '0xe2e429949e97f2e31cd82facd0a7ae38f65e2f38',
    '0xd1bf222ef7289ae043b723939d86c8a91f3aac3f',
    '0xE0902284c85A9A03dAA3B5ab032e238cc05CFF9a',
    '0x0052D7B657553E7f47239d8c4431Fef001A7f99c'
]

def check_succesful_tx(web3: Web3, txid: str, timeout=180) -> dict:
    """See if transaction went through (Solidity code did not throw).
    :return: Transaction receipt
    """
    receipt = wait_for_transaction_receipt(web3, txid, timeout=timeout)
    txinfo = web3.eth.getTransaction(txid)
    assert txinfo["gas"] != receipt["gasUsed"]
    return receipt


def wait(transfer_filter):
    with Timeout(30) as timeout:
        while not transfer_filter.get(False):
            timeout.sleep(2)


def main():
    project = Project()
    # chain_name = "testrpc"
    chain_name = "kovan"
    print("Make sure {} chain is running, you can connect to it, or you'll get timeout".format(chain_name))

    with project.get_chain(chain_name) as chain:
        web3 = chain.web3
        print("Web3 provider is", web3.currentProvider)

        token = chain.provider.get_contract_factory("RDNToken")
        txhash = token.deploy(args=[100000, "RDNToken", 6, "RDN"])
        receipt = check_succesful_tx(chain.web3, txhash, 250)
        token_addr = receipt["contractAddress"]
        print("RDNToken address is", token_addr)

        channel_factory = chain.provider.get_contract_factory("RaidenMicroTransferChannels")
        txhash = channel_factory.deploy(args=[token_addr, 30])
        receipt = check_succesful_tx(chain.web3, txhash, 250)
        cf_address = receipt["contractAddress"]
        print("RaidenMicroTransferChannels address is", cf_address)

        for sender in senders:
            token(token_addr).transact({"from": web3.eth.accounts[1]}).transfer(sender, 20000);


if __name__ == "__main__":
    main()
