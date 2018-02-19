from werkzeug.datastructures import EnvironHeaders
from eth_utils import to_checksum_address
from eth_utils import is_address
from microraiden import HTTPHeaders as header


class RequestData:
    def __init__(self, headers, cookies=None):
        """parse a flask request object and check if the data received are valid"""
        assert isinstance(headers, EnvironHeaders)
        self.update_from_headers(headers)
        if cookies:
            self.update_from_cookies(cookies)

    def update_from_cookies(self, cookies):
        if header.BALANCE_SIGNATURE in cookies:
            self.balance_signature = cookies.get(header.BALANCE_SIGNATURE)
        if header.OPEN_BLOCK in cookies:
            self.open_block_number = int(cookies.get(header.OPEN_BLOCK))
        if header.SENDER_BALANCE in cookies:
            self.balance = int(cookies.get(header.SENDER_BALANCE))
        if header.SENDER_ADDRESS in cookies:
            self.sender_address = cookies.get(header.SENDER_ADDRESS)

    def update_from_headers(self, headers):
        """Check if headers sent by the client are valid"""
        self.contract_address = headers.get(header.CONTRACT_ADDRESS, None)
        self.receiver_address = headers.get(header.RECEIVER_ADDRESS, None)
        self.sender_address = headers.get(header.SENDER_ADDRESS, None)
        self.payment = headers.get(header.PAYMENT, None)
        self.balance_signature = headers.get(header.BALANCE_SIGNATURE, None)
        open_block_number = headers.get(header.OPEN_BLOCK, None)
        if open_block_number:
            open_block_number = int(open_block_number)
        self.open_block_number = open_block_number
        balance = headers.get(header.BALANCE, None)
        if balance:
            balance = int(balance)
        self.balance = balance
        price = headers.get(header.PRICE, None)
        if price:
            price = int(price)
        self.price = price

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value: int):
        if value and value < 0:
            raise ValueError("Price must be >= 0")
        self._price = value

    @property
    def contract_address(self):
        return self._contract_address

    @contract_address.setter
    def contract_address(self, v: str):
        if v and is_address(v):
            self._contract_address = to_checksum_address(v)
        elif v:
            raise ValueError("Invalid contract address")
        else:
            self._contract_address = v

    @property
    def receiver_address(self):
        return self._receiver_address

    @receiver_address.setter
    def receiver_address(self, v: str):
        if v and is_address(v):
            self._receiver_address = to_checksum_address(v)
        elif v:
            raise ValueError("Invalid receiver address")
        else:
            self._receiver_address = v

    @property
    def sender_address(self):
        return self._sender_address

    @sender_address.setter
    def sender_address(self, v: str):
        if v and is_address(v):
            self._sender_address = to_checksum_address(v)
        elif v:
            raise ValueError("Invalid sender address")
        else:
            self._sender_address = v

    @property
    def payment(self):
        return self._payment

    @payment.setter
    def payment(self, v):
        if v and isinstance(v, int):
            if v < 0:
                raise ValueError('Payment must be > 0')
        elif v:
            raise ValueError("Payment must be an integer")
        self._payment = v

    @property
    def open_block_number(self):
        return self._open_block_number

    @open_block_number.setter
    def open_block_number(self, v: int):
        if v and not isinstance(v, int):
            raise ValueError("Open block must be an integer")
        if v and v < 0:
            raise ValueError("Open block must be >= 0")
        self._open_block_number = v

    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, v: int):
        if v and not isinstance(v, int):
            raise ValueError("Balance must be an integer")
        if v and v < 0:
            raise ValueError("Balance must be >= 0")
        self._balance = v
