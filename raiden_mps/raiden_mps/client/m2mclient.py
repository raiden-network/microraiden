import requests
from ethereum.utils import encode_hex

from client.channel_info import ChannelInfo
from client.rmp_client import RMPClient
from raiden_mps.header import HTTPHeaders

STATUS_OK = 200
STATUS_PAYMENT_REQUIRED = 402
CHANNEL_SIZE_FACTOR = 3
HEADERS = HTTPHeaders.as_dict()


class M2MClient(object):
    def __init__(
            self,
            api_endpoint,
            api_port,
            datadir,
            rpc_endpoint,
            rpc_port,
            key_path,
            dry_run,
            channel_manager_address,
            contract_abi_path,
            token_address
    ):
        self.rmp_client = RMPClient(
            datadir,
            rpc_endpoint,
            rpc_port,
            key_path,
            dry_run,
            channel_manager_address,
            contract_abi_path,
            token_address
        )
        self.api_endpoint = api_endpoint
        self.api_port = api_port

    def request_resource(self, resource):
        """
        Requests a resource from the HTTP server. Required payment is performed via an existing or a new channel.
        """
        status, headers, body = self.perform_request(resource)
        if status == STATUS_PAYMENT_REQUIRED:
            channel_manager_address = headers[HEADERS['contract_address']]
            if channel_manager_address != self.rmp_client.channel_manager_address:
                print('Invalid channel manager address requested ({}). Aborting.'.format(channel_manager_address))
                return None

            price = int(headers[HEADERS['price']])
            print('Preparing payment of price {}.'.format(price))
            channel = self.perform_payment(headers[HEADERS['receiver_address']], price)
            if channel:
                status, headers, body = self.perform_request(resource, channel)

                if status == STATUS_OK:
                    # TODO: use actual cost
                    # print('Resource payment successful. Final cost: {}'.format(headers[HEADERS['cost']]))
                    print('Resource payment successful. Final cost: {}'.format(0))
                elif status == STATUS_PAYMENT_REQUIRED:
                    if HEADERS['insuf_funds'] in headers:
                        print('Error: Insufficient funds in channel for presented balance proof.')
                    elif HEADERS['insuf_confs'] in headers:
                        print(
                            'Error: Newly created channel does not have enough confirmations yet. Waiting for {} more.'
                                .format(headers[HEADERS['insuf_confs']])
                        )
                    else:
                        print('Error: Unknown error.')
            else:
                print('Error: Could not perform the payment.')

        else:
            print('Error code {} while requesting resource: {}'.format(status, body))

    def perform_payment(self, receiver, value):
        """
        Attempts to perform a payment on an existing channel or a new one if none is available.
        """
        # TODO: topup instead of creation if insufficiently funded.
        channels = [
            channel for channel in self.rmp_client.channels
            if channel.sender.lower() == self.rmp_client.account.lower() and
            channel.receiver.lower() == receiver.lower() and
            channel.state == ChannelInfo.State.open and channel.deposit - channel.balance > value
        ]
        if len(channels) > 1:
            print('Warning: {} open channels found. Choosing a random one.'.format(len(channels)))

        if channels:
            channel = channels[0]
            print('Found open channel, opened at block #{}.'.format(channel.block))
        else:
            deposit = CHANNEL_SIZE_FACTOR * value
            channel = self.rmp_client.open_channel(receiver, deposit)

        if channel:
            self.rmp_client.create_transfer(channel, value)
            return channel
        else:
            return None

    def perform_request(self, resource, channel=None):
        """
        Performs a simple GET request to the HTTP server with headers representing the given channel state.
        """
        if channel:
            headers = {
                HEADERS['contract_address']: self.rmp_client.channel_manager_address,
                HEADERS['balance']: str(channel.balance),
                HEADERS['balance_signature']: encode_hex(channel.balance_sig),
                HEADERS['sender_address']: channel.sender,
                HEADERS['receiver_address']: channel.receiver,
                HEADERS['open_block']: str(channel.block)
            }
        else:
            headers = None
        url = 'http://{}:{}/{}'.format(self.api_endpoint, self.api_port, resource)
        response = requests.get(url, headers=headers)
        return response.status_code, response.headers, response.content
