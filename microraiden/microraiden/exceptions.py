class MicroRaidenException(Exception):
    """Base exception for uRaiden"""
    pass


class InvalidBalanceAmount(MicroRaidenException):
    """Raised if the payment contains lesser balance than the previous one."""
    pass


class InvalidBalanceProof(MicroRaidenException):
    """Balance proof data do not make sense."""
    pass


class NoOpenChannel(MicroRaidenException):
    """Attempt to use nonexisting channel."""
    pass


class InsufficientConfirmations(MicroRaidenException):
    """uRaiden channel doesn't have enough confirmations."""
    pass


class NoBalanceProofReceived(MicroRaidenException):
    """Attempt to close channel with no registered payments."""
    pass


class InvalidContractVersion(MicroRaidenException):
    """Library is not compatible with the deployed contract version"""
    pass


class StateFileException(MicroRaidenException):
    """Base exception class for state file (database) operations"""
    pass


class StateContractAddrMismatch(StateFileException):
    """Stored state contract address doesn't match."""
    pass


class StateReceiverAddrMismatch(StateFileException):
    """Stored state receiver address doesn't match."""
    pass


class StateFileLocked(StateFileException):
    """Another process is already using the database"""
    pass


class InsecureStateFile(StateFileException):
    """Permissions of the state file do not match (0600 is expected)."""
    pass


class NetworkIdMismatch(StateFileException):
    """RPC endpoint and database have different network id."""
    pass
