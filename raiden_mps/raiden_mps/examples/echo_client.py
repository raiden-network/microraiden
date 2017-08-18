"""
This is dummy code showing how the minimal app could look like.
"""
import click
import re
from raiden_mps.client.rmp_client import RMPClient
from raiden_mps.client.m2m_client import M2MClient
import logging
import requests


@click.command()
@click.option('--key-path', required=True, help='Path to private key file.')
@click.option('--resource', required=True, help='Get this resource.')
def run(key_path, resource):
    # create the client
    rmp_client = RMPClient(key_path=key_path)
    client = M2MClient(
        rmp_client,
        'localhost',
        5000
    )

    # Get the resource. If payment is required, client will attempt to create
    # a channel or will use existing one.
    status, headers, body = client.request_resource(resource)
    if status == requests.codes.OK:
        if re.match('^text\/', headers['Content-Type']):
            logging.info("got the resource %s type=%s\n%s" % (
                resource,
                headers.get('Content-Type', '???'),
                body.decode()))
        else:
            logging.info("got the resource %s type=%s" % (
                resource,
                headers.get('Content-Type', '???')))
    else:
        logging.error("error getting the resource. code=%d body=%s" %
                      (status, body.decode().strip()))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run()
