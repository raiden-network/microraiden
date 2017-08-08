class PaymentInfo:
    def __init__(self, gateway, price, contract, sender, receiver, cost=None):
        self.gateway = gateway
        self.price = price
        self.cost = cost if cost else price
        self.contract = contract
        self.sender = sender
        self.receiver = receiver

    @staticmethod
    def from_header(header):
        gateway = header['RDN-Gateway-Path'] if 'RDN-Gateway-Path' in header else None
        price = header['RDN-Price'] if 'RDN-Price' in header else None
        cost = header['RDN-Cost'] if 'RDN-Cost' in header else None
        contract = header['RDN-Contract'] if 'RDN-Contract' in header else None
        sender = header['RDN-Sender-Address'] if 'RDN-Sender-Address' in header else None
        receiver = header['RDN-Receiver-Address'] if 'RDN-Receiver-Address' in header else None

        return PaymentInfo(gateway, price, contract, sender, receiver, cost)
