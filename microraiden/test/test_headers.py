import pytest  # noqa: F401

from microraiden import HTTPHeaders


def test_headers():
    TEST_SENDER_ADDR = '0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    TEST_RECEIVER_ADDR = '0xffffffffffffffffffffffffffffffffffffffff'
    headers_dict = {
        'Content-Type': 'application/json',
        'RDN-Cost': '5',
        'RDN-Receiver-Address': TEST_RECEIVER_ADDR
    }

    headers = HTTPHeaders.deserialize(headers_dict)
    assert headers.cost == '5'
    assert headers.receiver_address == TEST_RECEIVER_ADDR
    assert 'sender_address' not in headers

    headers_dict = HTTPHeaders.serialize(headers)
    assert len(headers_dict) == 2
    assert headers_dict['RDN-Cost'] == '5'
    assert headers_dict['RDN-Receiver-Address'] == TEST_RECEIVER_ADDR

    headers.sender_address = TEST_SENDER_ADDR
    assert headers.sender_address == TEST_SENDER_ADDR
    headers_dict = HTTPHeaders.serialize(headers)
    assert len(headers_dict) == 3
    assert headers_dict['RDN-Sender-Address'] == TEST_SENDER_ADDR
