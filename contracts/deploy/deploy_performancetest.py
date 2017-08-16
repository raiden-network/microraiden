"""
A simple Python script to deploy contracts and then do a smoke test for them.
"""
from populus import Project
from populus.utils.wait import wait_for_transaction_receipt
from web3 import Web3
from web3.utils.compat import (
    Timeout,
)
from ecdsa import SigningKey, SECP256k1
import sha3
import sign
import binascii
from ethereum.utils import encode_hex


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


def createWallet():
    keccak = sha3.keccak_256()
    priv = SigningKey.generate(curve=SECP256k1)
    pub = priv.get_verifying_key().to_string()
    keccak.update(pub)
    address = keccak.hexdigest()[24:]
    return (encode_hex(priv.to_string()), address)


def getTokens(amount_total):
    project = Project()
#    chain_name = "testrpc"
    chain_name = "kovan"
    print("Make sure {} chain is running, you can connect to it, or you'll get timeout".format(chain_name))

    with project.get_chain(chain_name) as chain:
        web3 = chain.web3
        print("Web3 provider is", web3.currentProvider)

        token = chain.provider.get_contract_factory("RDNToken")
        txhash = token.deploy(args=[amount_total, "RDNToken", 6, "RDN"])
        receipt = check_succesful_tx(chain.web3, txhash, 250)
        token_addr = receipt["contractAddress"]
        print("RDNToken address is", token_addr)

        channel_factory = chain.provider.get_contract_factory("RaidenMicroTransferChannels")
        txhash = channel_factory.deploy(args=[token_addr, 30])
        receipt = check_succesful_tx(chain.web3, txhash, 250)
        cf_address = receipt["contractAddress"]
        print("RaidenMicroTransferChannels address is", cf_address)

        priv_keys = []
        addresses = []
        # we cannot retrieve private keys from configured chains
        # therefore: create 5 wallets (sample addresses with private keys)
        # store in separate arrays
        for i in range(4):
            priv_key, address = createWallet()
            priv_keys.append(priv_key)
            addresses.append("0x" + address)

        # send 20000 ETH to each new wallet
        for sender in addresses:
            token(token_addr).transact({"from": web3.eth.accounts[0]}).transfer(sender, int(amount_total/10))

        # check if it works:
        # 1. get message balance hash for address[0]
        hash = channel_factory(cf_address).call().balanceMessageHash(addresses[0], 100, 10000)
        # 2. sign the hash with private key corresponding to address[0]
        hash_sig, addr = sign.check(bytes(hash, "raw_unicode_escape"), binascii.unhexlify(priv_keys[0]))
        # 3. check if ECVerify and ec_recovered address are equal
        ec_recovered_addr = channel_factory(cf_address).call().verifyBalanceProof(addresses[0], 100, 10000, hash_sig)
        print("EC_RECOVERED_ADDR:", ec_recovered_addr)
        print("FIRST WALLET ADDR:", addresses[0])
        assert ec_recovered_addr == addresses[0]
        print("BALANCE:", token(token_addr).call().balanceOf(addresses[0]))
        assert token(token_addr).call().balanceOf(addresses[0]) > 0

    # return arrays with generated wallets (private keys first, then addresses, so that priv_key[0] <-> address[0]
    return (priv_keys, addresses, token(token_addr))

if __name__ == "__main__":
    print(getTokens(10000000))
