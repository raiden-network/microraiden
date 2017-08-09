"""
This is dummy code showing how the minimal app could look like.
"""
from raiden_mps.client import PayWallClient


client = PayWallClient(keystore='')
r = client.get(url='http://localhost/echo/hello')
print(r)
b = client.channel.info
print(b)
