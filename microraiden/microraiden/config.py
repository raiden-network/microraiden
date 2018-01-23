from eth_utils import denoms
from collections import namedtuple, OrderedDict
from functools import partial

# these are default values for network config
network_config_defaults = OrderedDict(
    (('channel_manager_address', None),
     ('start_sync_block', 0),
     ('gas_price', 20 * denoms.gwei),
     ('gas_limit', 130000),
     # pot = plain old transaction, for lack of better term
     ('pot_gas_limit', 21000))
)
# create network config type that supports defaults
NetworkConfig = partial(
    namedtuple(
        'NetworkConfig',
        network_config_defaults
    ),
    **network_config_defaults
)

# network-specific configuration
NETWORK_CONFIG_DEFAULTS = {
    # mainnet
    1: NetworkConfig(
        channel_manager_address='0x1440317CB15499083dEE3dDf49C2bD51D0d92e33',
        start_sync_block=4958602,
        gas_price=20 * denoms.gwei
    ),
    # ropsten
    3: NetworkConfig(
        channel_manager_address='0x74434527b8e6c8296506d61d0faf3d18c9e4649a',
        start_sync_block=2507629
    ),
    # rinkeby
    4: NetworkConfig(
        channel_manager_address='0xbec8fb898e6da01152576d1a1acdd2c957e56fb1',
        start_sync_block=1642336
    ),
    # kovan
    42: NetworkConfig(
        channel_manager_address='0xed94e711e9de1ff1e7dd34c39f0d4338a6a6ef92',
        start_sync_block=5523491
    ),
    # internal - used only with ethereum tester
    65536: NetworkConfig(
        channel_manager_address='0x0',
        start_sync_block=0
    )
}


class NetworkRuntime:
    def __init__(self):
        super().__setattr__('cfg', None)

    def set_defaults(self, network_id: int):
        cfg_copy = dict(NETWORK_CONFIG_DEFAULTS[network_id]._asdict())
        super().__setattr__('cfg', cfg_copy)

    def __getattr__(self, attr):
        return self.cfg.__getitem__(attr.lower())

    def __setattr__(self, attr, value):
        if attr == 'cfg':
            return super().__setattr__('cfg', value)
        return self.cfg.__setitem__(attr.lower(), value)


def get_defaults(network_id: int):
    return NETWORK_CONFIG_DEFAULTS[network_id]


# default config is ropsten
NETWORK_CFG = NetworkRuntime()
NETWORK_CFG.set_defaults(3)
