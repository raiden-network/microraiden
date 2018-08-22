MAX_UINT256 = 2 ** 256 - 1
MAX_UINT192 = 2 ** 192 - 1
MAX_UINT32 = 2 ** 32 - 1

CHANNEL_DEPOSIT_BUGBOUNTY_LIMIT = 100 * 10 ** 18
URAIDEN_CONTRACT_VERSION = '0.2.0'

CHALLENGE_PERIOD_MIN = 500

PASSPHRASE = '0'
FAKE_ADDRESS = '0x03432'

EMPTY_ADDRESS = '0x0000000000000000000000000000000000000000'

URAIDEN_EVENTS = {
    'created': 'ChannelCreated',
    'topup': 'ChannelToppedUp',
    'closed': 'ChannelCloseRequested',
    'settled': 'ChannelSettled',
    'withdraw': 'ChannelWithdraw',
    'trusted': 'TrustedContract'
}
