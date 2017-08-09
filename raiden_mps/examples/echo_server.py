"""
This is dummy code showing how the minimal app could look like.
In his case we don't use a proxy, but directly a server
"""
from raiden_mps.server import PayWalledServer


@app.route('/echo/<param>', price=23423)
def echo(param):
    return param


def cost_func(param):
    return 100 * len(param)


@app.route('/echo2/<param>', price=cost_func)
def echo2(param):
    return param

if __name__ == '__main__':
    app = PayWalledServer(keystore='', micropayment_contract='')
    app.run()
