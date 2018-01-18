from typing import List, Any, Union, Dict

import gevent
import rlp
from eth_utils import decode_hex, encode_hex
from ethereum.transactions import Transaction
from web3 import Web3
from web3.contract import Contract

from microraiden.config import NETWORK_CFG
from microraiden.utils import privkey_to_addr, sign_transaction
from microraiden.utils.populus_compat import LogFilter

DEFAULT_TIMEOUT = 60
DEFAULT_RETRY_INTERVAL = 3


def create_signed_transaction(
        private_key: str,
        web3: Web3,
        to: str,
        value: int=0,
        data=b'',
        nonce_offset: int = 0,
        gas_price: Union[int, None] = None,
        gas_limit: int = NETWORK_CFG.POT_GAS_LIMIT
) -> str:
    """
    Creates a signed on-chain transaction compliant with EIP155.
    """
    if gas_price is None:
        gas_price = NETWORK_CFG.GAS_PRICE
    tx = create_transaction(
        web3=web3,
        from_=privkey_to_addr(private_key),
        to=to,
        value=value,
        data=data,
        nonce_offset=nonce_offset,
        gas_price=gas_price,
        gas_limit=gas_limit
    )
    sign_transaction(tx, private_key, int(web3.version.network))
    return encode_hex(rlp.encode(tx))


def create_transaction(
        web3: Web3,
        from_: str,
        to: str,
        data: bytes = b'',
        nonce_offset: int = 0,
        value: int = 0,
        gas_price: Union[int, None] = None,
        gas_limit: int = NETWORK_CFG.POT_GAS_LIMIT
) -> Transaction:
    if gas_price is None:
        gas_price = NETWORK_CFG.GAS_PRICE
    nonce = web3.eth.getTransactionCount(from_, 'pending') + nonce_offset
    tx = Transaction(nonce, gas_price, gas_limit, to, value, data)
    tx.sender = decode_hex(from_)
    return tx


def create_signed_contract_transaction(
        private_key: str,
        contract: Contract,
        func_name: str,
        args: List[Any],
        value: int=0,
        nonce_offset: int = 0,
        gas_price: Union[int, None] = None,
        gas_limit: int = NETWORK_CFG.GAS_LIMIT
) -> str:
    """
    Creates a signed on-chain contract transaction compliant with EIP155.
    """
    if gas_price is None:
        gas_price = NETWORK_CFG.GAS_PRICE
    tx = create_contract_transaction(
        contract=contract,
        from_=privkey_to_addr(private_key),
        func_name=func_name,
        args=args,
        value=value,
        nonce_offset=nonce_offset,
        gas_price=gas_price,
        gas_limit=gas_limit
    )
    sign_transaction(tx, private_key, int(contract.web3.version.network))
    return encode_hex(rlp.encode(tx))


def create_contract_transaction(
        contract: Contract,
        from_: str,
        func_name: str,
        args: List[Any],
        value: int = 0,
        nonce_offset: int = 0,
        gas_price: Union[int, None] = None,
        gas_limit: int = NETWORK_CFG.GAS_LIMIT
) -> Transaction:
    if gas_price is None:
        gas_price = NETWORK_CFG.GAS_PRICE
    data = create_transaction_data(contract, func_name, args)
    return create_transaction(
        web3=contract.web3,
        from_=from_,
        to=contract.address,
        value=value,
        data=data,
        nonce_offset=nonce_offset,
        gas_price=gas_price,
        gas_limit=gas_limit
    )


def create_transaction_data(contract: Contract, func_name: str, args: List[Any]) -> bytes:
    data = contract._prepare_transaction(func_name, args)['data']
    return decode_hex(data)


def get_logs(
        contract: Contract,
        event_name: str,
        from_block: Union[int, str] = 0,
        to_block: Union[int, str] = 'pending',
        argument_filters: Dict[str, Any] = None
):
    event_abi = [
        abi_element for abi_element in contract.abi
        if abi_element['type'] == 'event' and abi_element['name'] == event_name
    ]
    assert len(event_abi) == 1, 'No event found matching name {}.'.format(event_name)
    event_abi = event_abi[0]

    if argument_filters is None:
        argument_filters = {}

    tmp_filter = LogFilter(
        contract.web3,
        [event_abi],
        contract.address,
        event_name,
        from_block,
        to_block,
        argument_filters
    )
    return tmp_filter.get_logs()


def _get_logs_raw(contract: Contract, filter_params: Dict[str, Any]):
    """For easy patching."""
    return contract.web3._requestManager.request_blocking('eth_getLogs', [filter_params])


def get_event_blocking(
        contract: Contract,
        event_name: str,
        from_block: Union[int, str] = 0,
        to_block: Union[int, str] = 'latest',
        argument_filters: Dict[str, Any]=None,
        condition=None,
        wait=DEFAULT_RETRY_INTERVAL,
        timeout=DEFAULT_TIMEOUT
) -> Union[Dict[str, Any], None]:
    for i in range(0, timeout + wait, wait):
        logs = get_logs(
            contract,
            event_name,
            from_block=from_block,
            to_block=to_block,
            argument_filters=argument_filters
        )
        matching_logs = [event for event in logs if not condition or condition(event)]
        if matching_logs:
            return matching_logs[0]
        elif i < timeout:
            _wait(wait)

    return None


def _wait(duration: float):
    """For easy patching."""
    gevent.sleep(duration)


def wait_for_transaction(
        web3: Web3,
        tx_hash: str,
        timeout: int = DEFAULT_TIMEOUT,
        polling_interval: int = DEFAULT_RETRY_INTERVAL
):
    for waited in range(0, timeout + polling_interval, polling_interval):
        tx_receipt = web3.eth.getTransactionReceipt(tx_hash)
        if tx_receipt is not None:
            return tx_receipt
        if waited < timeout:
            _wait(polling_interval)
    raise TimeoutError('Transaction {} was not mined.'.format(tx_hash))
