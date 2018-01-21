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
    1: NetworkConfig(
        channel_manager_address='0x4d6e0922e6b703f0fdf92745343a9b83eb656402',
        start_sync_block=4651176,
        gas_price=20 * denoms.gwei
    ),
    3: NetworkConfig(
        channel_manager_address='0x161a0d7726EB8B86EB587d8BD483be1CE87b0609',
        start_sync_block=2400640
    ),
    4: NetworkConfig(
        channel_manager_address='0x568a0d52a173f584d4a286a22b2a876911079e15',
        start_sync_block=1338285
    ),
    42: NetworkConfig(
        channel_manager_address='0xB9721dF0e024114e7B25F2cF503d8CBE3D52b400',
        start_sync_block=5230017
    ),
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
