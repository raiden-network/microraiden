from eth_utils import denoms
from web3 import Web3
from web3.utils.empty import empty as web3_empty

from microraiden.utils import create_signed_transaction, wait_for_transaction


def test_create_signed_transaction():
    # Mock to simulate the example from EIP 155.
    # https://github.com/ethereum/EIPs/blob/master/EIPS/eip-155.md#list-of-chain-ids
    class Web3Mock:
        class VersionMock:
            network = 1

        class EthMock:
            class ContractMock:
                def _prepare_transaction(self, *args, **kwargs):
                    return {'data': b''}

            defaultAccount = web3_empty

            def contract(self, *args, **kwargs):
                return self.ContractMock()

            def getTransactionCount(self, *args, **kwargs):
                return 9

            def getCode(self, *args, **kwargs):
                """Need to implement this to fake contract existence check"""
                return '0x123456789abcdef'

        version = VersionMock()
        eth = EthMock()

    # TODO: replace with proper mock
    web3 = Web3Mock()
    private_key = '0x4646464646464646464646464646464646464646464646464646464646464646'
    address = '0x3535353535353535353535353535353535353535'

    tx = create_signed_transaction(
        private_key,
        web3,
        to=address,
        value=10**18,
        gas_limit=21000,
        gas_price=20 * denoms.gwei
    )
    tx_expected = \
        '0xf86c098504a817c800825208943535353535353535353535353535353535353535880de0' \
        'b6b3a76400008025a028ef61340bd939bc2195fe537567866003e1a15d3c71ff63e1590620' \
        'aa636276a067cbe9d8997f761aecb703304b3800ccf555c9f3dc64214b297fb1966a3b6d83'
    assert tx == tx_expected


def test_wait_for_transaction(
        web3: Web3,
        patched_contract,
        receiver_address: str,
        faucet_private_key: str,
):
    tx = create_signed_transaction(
        faucet_private_key,
        web3,
        to=receiver_address
    )
    tx_hash = web3.eth.sendRawTransaction(tx)
    tx_receipt = wait_for_transaction(web3, tx_hash)
    assert tx_receipt
