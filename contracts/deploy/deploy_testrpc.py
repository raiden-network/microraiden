"""
A simple Python script to deploy contracts and then do a smoke test for them.
"""
from populus import Project
from populus.utils.wait import wait_for_transaction_receipt
from web3 import Web3
from web3.utils.compat import (
    Timeout,
)

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
    chain_name = "testrpc"
    print("Make sure {} chain is running, you can connect to it, or you'll get timeout".format(chain_name))

    with project.get_chain(chain_name) as chain:
        web3 = chain.web3
        print("Web3 provider is", web3.currentProvider)

        token = chain.provider.get_contract_factory("RDNToken")
        txhash = token.deploy(args=[1000, "RDNToken", 6, "RDN"])
        receipt = check_succesful_tx(chain.web3, txhash)
        token_addr = receipt["contractAddress"]
        print("RDNToken address is", token_addr)

        channel_factory = chain.provider.get_contract_factory("RaidenPaymentChannel")
        txhash = channel_factory.deploy()
        receipt = check_succesful_tx(chain.web3, txhash)
        cf_address = receipt["contractAddress"]
        print("RaidenPaymentChannel address is", cf_address)

        # approve 100 to contract
        token(token_addr).transact({"from": web3.eth.accounts[0]}).approve(cf_address, 90);

        transfer_filter = channel_factory(cf_address).on('ChannelCreated')
        txhash = channel_factory(cf_address).transact({"from": web3.eth.accounts[0]}).init(web3.eth.accounts[1], token_addr, 90, 10)
        check_succesful_tx(web3, txhash)
        wait(transfer_filter)
        log_entries = transfer_filter.get()
        print(log_entries[0]['args']['_sender'])
        print(log_entries[0]['args']['_receiver'])
        print(log_entries[0]['args']['_id'])

if __name__ == "__main__":
    main()
