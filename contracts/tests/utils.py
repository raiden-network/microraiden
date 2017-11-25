from utils.sign import eth_signed_typed_data_message


def balance_proof_hash(receiver, block, balance):
    return eth_signed_typed_data_message(
        ('address', ('uint', 32), ('uint', 192)),
        ('receiver', 'block_created', 'balance'),
        (receiver, block, balance)
    )
