from server import ChannelManagerState

class ChannelManagerMock(object):

    def __init__(self, receiver, blockchain, state_filename=None, init_contract_address=None):
        self.receiver = receiver
        self.blockchain = blockchain
        if init_contract_address:
            self.state = ChannelManagerState(init_contract_address, receiver)
        else:
            assert state_filename is not None
            self.state = self.state.load(state_filename)

    def set_head(self, number, _hash):
        "should be called by blockchain after all events have been delivered, to trigger store"
        self.state.head_number = number
        self.state.head_hash = _hash
        self.state.store()

    # relevant events from the blockchain for receiver from contract

    def event_channel_opened(self, sender, deposit):
        assert sender not in self.state.channels  # shall we allow top-ups
        c = Channel(self.receiver, sender, deposit)
        self.state.channels[sender] = c

    def event_channel_close_requested(self, sender, balance, settle_timeout):
        "channel was closed by sender without consent"
        assert sender in self.state.channels
        c = self.state.channels[sender]
        if c.balance > balance:
            self.close_channel(sender)  # dispute by closing the channel
        else:
            c.settle_timeout = settle_timeout
            c.is_closed = True
        self.state.store()

    def event_channel_settled(self, sender):
        del self.state.channels[sender]
        self.state.store()

    # end events ####

    def close_channel(self, sender):
        "receiver can always close the channel directly"
        c = self.state.channels[sender]

        # prepare and send close tx
        signature = generate_signature(c, private_key)
        data = contract._encode_transaction_data('close', sender, c.open_block_number,
                                                  c.balance, signature)
#        tx = Transaction(**{
#            'nonce': self.web3.eth.getTransactionCount(self.receiver),
#            'value': 0,
#            'to': self.contract_address,
#            'gasprice': 0,
#            'startgas': 0,
#            'data': data
#        })
#        tx.sign(self.private_key)
#        self.web3.eth.sendRawTransaction(web3.toHex(rlp.encode(tx)))

        # update local state
        c.is_closed = True
        self.state.store()

    def sign_close(self, sender):
        c = self.state.channels[sender]
        c.is_closed = True
        lm = c.last_message
        # return signed lm
        self.state.store()

    def get_token_balance(self):
        balance = 0
        for channel in self.state.channels.values():
            balance += channel.balance
        return balance

    def register_payment(self, msg):
        """
        registers a payment message
        returns its sender and value
        """
        sender, balance = parse_balance_proof_msg(msg)
        assert sender in self.state.channels
        c = self.state.channels[sender]
        assert c.balance < balance
        received = balance - c.balance
        c.balance = balance
        c.last_message = msg
        c.mtime = time.time()
        self.state.store()
        return (sender, received)
