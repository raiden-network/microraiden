"""
This is dummy code showing how the minimal app could look like.
"""
from microraiden.server import PayWallProxy


def cost_func(request):
    return 100 * len(request.args['someinput'])


path_cost = {
    '/echo/': 66,
    '/echo/': cost_func,
}


if __name__ == '__main__':
    app = PayWallProxy(keystore='',
                       micropayment_contract='',
                       path_cost=path_cost
                       )
    app.run()
