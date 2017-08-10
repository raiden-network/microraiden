class HTTPHeaders():
    PRICE = 'RDN-Price'
    CONTRACT_ADDRESS = 'RDN-Contract-Address'
    RECEIVER_ADDRESS = 'RDN-Receiver-Address'
    PAYMENT = 'RDN-Payment'
    BALANCE = 'RDN-Balance'
    BALANCE_SIGNATURE = 'RDN-Balance-Signature'
    SENDER_ADDRESS = 'RDN-Sender-Address'
    SENDER_BALANCE = 'RDN-Sender-Balance'
    GATEWAY_PATH = 'RDN-Gateway-Path'
    INSUF_FUNDS = 'RDN-Insufficient-Funds'
    INSUF_CONFS = 'RDN-Insufficient-Confirmations'
    COST = 'RDN-Cost'
    OPEN_BLOCK = 'RDN-Open-Block'

    @classmethod
    def as_dict(cls):
        return dict((k.lower(), v) for k, v in cls.__dict__.items() if str(v).startswith('RDN'))
