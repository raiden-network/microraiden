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


class StateFileException(MicroRaidenException):
    pass


class StateContractAddrMismatch(StateFileException):
    pass


class StateReceiverAddrMismatch(StateFileException):
    pass


class StateFileLocked(StateFileException):
    pass


class InsecureStateFile(StateFileException):
    pass


class NetworkIdMismatch(StateFileException):
    pass
