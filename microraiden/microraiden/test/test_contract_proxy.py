from web3.utils.empty import empty as web3_empty

from microraiden.contract_proxy import ContractProxy


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

        version = VersionMock()
        eth = EthMock()

    privkey = '0x4646464646464646464646464646464646464646464646464646464646464646'
    address = '0x3535353535353535353535353535353535353535'
    proxy = ContractProxy(Web3Mock(), privkey, address, None, 20 * 10 ** 9, 21000)

    tx = proxy.create_signed_transaction(None, None, value=10**18)
    tx_expected = \
        '0xf86c098504a817c800825208943535353535353535353535353535353535353535880de0b6b3a7640000' \
        '8025' \
        'a028ef61340bd939bc2195fe537567866003e1a15d3c71ff63e1590620aa636276' \
        'a067cbe9d8997f761aecb703304b3800ccf555c9f3dc64214b297fb1966a3b6d83'
    assert tx == tx_expected
