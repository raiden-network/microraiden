from typing import Dict
from munch import Munch


class HTTPHeaders(object):
    PRICE = 'RDN-Price'
    CONTRACT_ADDRESS = 'RDN-Contract-Address'
    RECEIVER_ADDRESS = 'RDN-Receiver-Address'
    TOKEN_ADDRESS = 'RDN-Token-Address'
    PAYMENT = 'RDN-Payment'
    BALANCE = 'RDN-Balance'
    BALANCE_SIGNATURE = 'RDN-Balance-Signature'
    SENDER_ADDRESS = 'RDN-Sender-Address'
    SENDER_BALANCE = 'RDN-Sender-Balance'
    GATEWAY_PATH = 'RDN-Gateway-Path'
    COST = 'RDN-Cost'
    OPEN_BLOCK = 'RDN-Open-Block'

# errors
    INSUF_CONFS = 'RDN-Insufficient-Confirmations'
    NONEXISTING_CHANNEL = 'RDN-Nonexisting-Channel'
    INVALID_PROOF = 'RDN-Invalid-Balance-Proof'
    INVALID_AMOUNT = 'RDN-Invalid-Amount'

    DESERIALIZE_DICT = None
    SERIALIZE_DICT = None

    @classmethod
    def as_dict(cls):
        return dict((k.lower(), v) for k, v in cls.__dict__.items() if str(v).startswith('RDN'))

    @classmethod
    def deserialize(cls, headers: Dict[str, str] = None) -> Munch:
        if not cls.DESERIALIZE_DICT:
            cls.DESERIALIZE_DICT = {
                v.lower(): k.lower() for k, v in HTTPHeaders.__dict__.items()
                if str(v).startswith('RDN')
            }

        return Munch({
            cls.DESERIALIZE_DICT[key.lower()]: value for key, value in headers.items()
            if key.lower() in cls.DESERIALIZE_DICT
        })

    @classmethod
    def serialize(cls, headers: Munch) -> Dict[str, str]:
        if not cls.SERIALIZE_DICT:
            cls.SERIALIZE_DICT = {
                k.lower(): v for k, v in HTTPHeaders.__dict__.items() if str(v).startswith('RDN')
            }
        return {cls.SERIALIZE_DICT[k]: v for k, v in headers.items() if v}
