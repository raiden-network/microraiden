import os
import stat


def parse_balance_proof_msg(proxy, receiver, open_block_number, balance, signature):
    return proxy.verifyBalanceProof(receiver, open_block_number, balance, signature)


def is_file_rwxu_only(path):
    f_stats = os.stat(path)
    return (f_stats.st_mode & (stat.S_IRWXG | stat.S_IRWXO)) == 0
