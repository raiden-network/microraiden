from microraiden.config import NETWORK_CFG, NETWORK_CONFIG_DEFAULTS
from microraiden.utils.contract import create_transaction

TEST_GAS_PRICE = 123456


def test_network_config():
    mainnet_gas_price = NETWORK_CONFIG_DEFAULTS[1].gas_price
    ropsten_gas_price = NETWORK_CONFIG_DEFAULTS[3].gas_price

    # don't forget to restore existing network config
    old_cfg = NETWORK_CFG.cfg

    NETWORK_CFG.set_defaults(1)
    assert NETWORK_CFG.gas_price == mainnet_gas_price
    NETWORK_CFG.gas_price = TEST_GAS_PRICE
    assert NETWORK_CFG.gas_price == TEST_GAS_PRICE
    NETWORK_CFG.set_defaults(1)
    assert NETWORK_CFG.gas_price == mainnet_gas_price
    NETWORK_CFG.set_defaults(3)
    assert NETWORK_CFG.gas_price == ropsten_gas_price

    NETWORK_CFG.cfg = old_cfg


def test_transaction_params(web3):
    old_cfg = NETWORK_CFG.cfg
    NETWORK_CFG.set_defaults(1)
    addr1 = '0x0000000000000000000000000000000000000001'
    addr2 = '0x0000000000000000000000000000000000000002'
    tx = create_transaction(web3, addr1, addr2)
    assert tx.gasprice == NETWORK_CFG.gas_price
    NETWORK_CFG.gas_price = TEST_GAS_PRICE
    tx = create_transaction(web3, addr1, addr2)
    assert tx.gasprice == TEST_GAS_PRICE
    NETWORK_CFG.cfg = old_cfg
