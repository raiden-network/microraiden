# Raiden MicroTransfer Channels Contract


- _Sender_ = token sender
- _Receiver_ = token receiver
- _Contract_ = Raiden MicroTransfer Channels Smart Contract

## Opening a transfer channel



- approve token transfers to the contract from the Sender's behalf:  `Token.approve(contract, deposit)`
- `Contract.createChannel(receiver, deposit)`



## Generating and validating a transfer


Sender has to provide a **balance proof**:
- **balance message**: `receiver`, `open_block_number`, `balance`
- **signed balance message**: `balance_msg_sig`
  - `Contract.balanceMessageHash(receiver, open_block_number, balance)` -> signed by the Sender with MetaMask


Balance proof signature verification:

 - `Contract.verifyBalanceProof(receiver, open_block_number, balance, balance_msg_sig)` -> returns the Sender's address



## Generating and validating a closing agreement


Sender has to provide a **balance proof** and a **closing agreement proof**
- **balance message**: `receiver`, `open_block_number`, `balance`
- **signed balance message**: `balance_msg_sig`
- **double signed balance message**: `closing_sig` - signed by both the sender and the receiver
 - `Contract.closingAgreementMessageHash(balance_msg_sig)`
 - Receiver signs this hash with MetaMask and sends it to the Sender


Closing agreement signature verification:

- `Contract.verifyClosingSignature(balance_msg_sig, closing_sig)` -> returns the Receiver's address


## Closing a channel


1. Receiver calls `Contract.close(receiver, open_block_number, balance, balance_msg_sig)` with the sender's signed balance message = instant close & settle
2. Client calls `Contract.close(receiver, open_block_number, balance, balance_msg_sig, closing_sig)` = instant close & settle
3. Client calls `Contract.close(receiver, open_block_number, balance, balance_msg_sig)` = settlement period starts
 - a. Receiver calls `Contract.close(receiver, open_block_number, balance, balance_msg_sig)` with the sender's signed balance message = instant close & settle
 - b. Client calls `Contract.settle(receiver, open_block_number)` after settlement period ends
