import pytest
import codecs
from populus.utils.wait import wait_for_transaction_receipt
from web3.utils.compat import (
    Timeout,
)
from ethereum import tester
import sign

from fixtures import (
    create_contract,
    token_contract,
    #contract,
    channels_contract,
    save_logs,
    get_gas_used,
    get_balance_message
)


def get_last_open_block_number(contract):
    add_logs(contract, 'ChannelCreated')
    created_logs = logs['ChannelCreated'][len(logs['ChannelCreated']) - 1]
    open_block_number = created_logs['blockNumber']
    return open_block_number


def add_logs(contract, event_name):
    logs[event_name] = []
    def add(log):
        logs[event_name].append(log)
    save_logs(contract, event_name, add)
    with Timeout(20) as timeout:
        timeout.sleep(2)


@pytest.fixture
def contract(chain, web3, token_contract, channels_contract):
    global token
    global logs
    global challenge_period
    challenge_period = 5
    logs = {}
    token = token_contract([10000, "ERC223Token", 2, "TKN"])
    contract = channels_contract([token.address, challenge_period])
    return contract


@pytest.fixture
def channel(contract, web3):
    (Owner, A, B) = web3.eth.accounts[:3]
    global channel_deposit
    channel_deposit = 220

    txdata = B[2:].zfill(40)
    txdata = bytes.fromhex(txdata)

    print('Owner', Owner)
    print('sender', A)
    print('receiver', B)
    print('ChannelsContract', contract.address)
    print('Token', token.address)

    token.transact({"from": Owner}).transfer(A, channel_deposit + 45)
    token.transact({"from": Owner}).transfer(B, 22)

    # Create channel
    token.transact({"from": A}).transfer(contract.address, channel_deposit, txdata)
    assert token.call().balanceOf(contract.address) == channel_deposit
    open_block_number = get_last_open_block_number(contract)

    return (A, B, open_block_number)


def test_sign(contract, channel):
    (sender, receiver, open_block_number) = channel
    balance = 23

    msg = get_balance_message(receiver, open_block_number, balance)
    # "Receiver: " + receiver + "\nBalance: " + str(balance) + "\nChannel ID: " + str(open_block_number)

    # hex: 0x19457468657265756d205369676e6564204d6573736167653a0a373852656365697665723a203078646365636561663366633563306136336431393564363962316139303031316237623139363530640a42616c616e63653a2032330a4368616e6e656c2049443a2035

    print('--- test_sign msg', msg)
    balance_msg_sig, addr = sign.check(msg, tester.k2)
    print('--balance_msg_sig', balance_msg_sig, addr)

    addr = contract.call().verifyBalanceProof(receiver, open_block_number, balance, balance_msg_sig)
    print('--verifyBalanceProof addr', addr)

    # with Timeout(20) as timeout:
    #     timeout.sleep(2)

    assert addr == receiver
