class HTTPHeaders:
    GATEWAY = 'RDN-Gateway-Path'
    PRICE = 'RDN-Price'
    COST = 'RDN-Cost'
    CONTRACT = 'RDN-Contract-Address'
    SENDER = 'RDN-Sender-Address'
    RECEIVER = 'RDN-Receiver-Address'
    INSUF_FUNDS = 'RDN-Insufficient-Funds'
    INSUF_CONFS = 'RDN-Insufficient-Confirmations'

    @classmethod
    def as_dict(cls):
        return dict((k.lower(), v) for k, v in cls.__dict__.items() if str(v).startswith('RDN'))
