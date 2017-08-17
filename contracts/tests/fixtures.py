import pytest


@pytest.fixture
def create_contract(chain):
    def get(contract_type, arguments, transaction=None):
        deploy_txn_hash = contract_type.deploy(transaction=transaction, args=arguments)
        contract_address = chain.wait.for_contract_address(deploy_txn_hash)
        contract = contract_type(address=contract_address)
        return contract
    return get


@pytest.fixture()
def token_contract(chain, create_contract):
    def get(arguments, transaction=None):
        RDNToken = chain.provider.get_contract_factory('RDNToken')
        token_contract = create_contract(RDNToken, arguments, transaction)

        print_logs(token_contract, 'Approval', 'RDNToken')
        print_logs(token_contract, 'Transfer', 'RDNToken')
        # print_logs(token_contract, 'GasCost', 'RDNToken')

        return token_contract
    return get


@pytest.fixture()
def channels_contract(chain, create_contract):
    def get(arguments, transaction=None):
        RaidenMicroTransferChannels = chain.provider.get_contract_factory('RaidenMicroTransferChannels')

        channels_contract = create_contract(RaidenMicroTransferChannels, arguments, transaction)

        print_logs(channels_contract, 'ChannelCreated', 'RaidenMicroTransferChannels')
        print_logs(channels_contract, 'ChannelToppedUp', 'RaidenMicroTransferChannels')
        print_logs(channels_contract, 'ChannelCloseRequested', 'RaidenMicroTransferChannels')
        print_logs(channels_contract, 'ChannelSettled', 'RaidenMicroTransferChannels')
        print_logs(channels_contract, 'GasCost', 'RaidenMicroTransferChannels')
        print_logs(channels_contract, 'TokenFallback', 'RaidenMicroTransferChannels')

        return channels_contract
    return get


def print_logs(contract, event, name=''):
    transfer_filter_past = contract.pastEvents(event)
    past_events = transfer_filter_past.get()
    if len(past_events):
        print('--(', name, ') past events for ', event, past_events)

    transfer_filter = contract.on(event)
    events = transfer_filter.get()
    if len(events):
        print('--(', name, ') events for ', event, events)

    transfer_filter.watch(lambda x: print('--(', name, ') event ', event, x['args']))


def save_logs(contract, event_name, add):
    transfer_filter_past = contract.pastEvents(event_name)
    past_events = transfer_filter_past.get()
    for event in past_events:
        add(event)

    transfer_filter = contract.on(event_name)

    events = transfer_filter.get()
    for event in events:
        add(event)
    transfer_filter.watch(lambda x: add(x))


def get_gas_used(chain, trxid):
    return chain.wait.for_receipt(trxid)["gasUsed"]


def print_gas_used(chain, trxid, message):
    print(message, get_gas_used(chain, trxid))


def wait(transfer_filter):
    with Timeout(30) as timeout:
        while not transfer_filter.get(False):
            timeout.sleep(2)
