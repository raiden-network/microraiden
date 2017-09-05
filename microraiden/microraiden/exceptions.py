class MicroRaidenException(Exception):
    pass


class InvalidBalanceAmount(MicroRaidenException):
    pass


class InvalidBalanceProof(MicroRaidenException):
    pass


class NoOpenChannel(MicroRaidenException):
    pass


class InsufficientConfirmations(MicroRaidenException):
    pass


class NoBalanceProofReceived(MicroRaidenException):
    pass


class StateContractAddrMismatch(MicroRaidenException):
    pass


class StateReceiverAddrMismatch(MicroRaidenException):
    pass


class StateFileLocked(MicroRaidenException):
    pass


class InsecureStateFile(MicroRaidenException):
    pass


class NetworkIdMismatch(MicroRaidenException):
    pass
