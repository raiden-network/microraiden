import functools
from web3.utils.events import get_event_data
from web3.utils.filters import construct_event_filter_params
from inspect import getframeinfo, stack
from web3.utils.threads import (
    Timeout,
)


class LogHandler:
    def __init__(self, web3, address, abi):
        self.web3 = web3
        self.address = address
        self.abi = abi
        self.event_waiting = {}
        self.event_filters = {}
        self.event_verified = []
        self.event_unkown = []

    def add(self, txn_hash, event_name, callback=None):
        caller = getframeinfo(stack()[1][0])
        message = "%s:%d" % (caller.filename, caller.lineno)

        if event_name not in self.event_waiting:
            self.event_waiting[event_name] = {}
            self.event_filters[event_name] = LogFilter(
                self.web3,
                self.abi,
                self.address,
                event_name,
                callback=self.handle_log
            )

        self.event_waiting[event_name][txn_hash] = [message, callback]

    def check(self, timeout=5):
        for event in list(self.event_filters.keys()):
            self.event_filters[event].init()

        self.wait(timeout)

    def handle_log(self, event):
        txn_hash = event['transactionHash']
        event_name = event['event']

        if event_name in self.event_waiting:
            if txn_hash in self.event_waiting[event_name]:
                self.event_verified.append(event)
                event_entry = self.event_waiting[event_name].pop(txn_hash, None)

                # Call callback function with event and remove
                if event_entry[1]:
                    event_entry[1](event)

            else:
                self.event_unkown.append(event)
            if not len(list(self.event_waiting[event_name].keys())):
                self.event_waiting.pop(event_name, None)
                self.event_filters.pop(event_name, None)

    def wait(self, seconds):
        try:
            with Timeout(seconds) as timeout:
                while len(list(self.event_waiting.keys())):
                    timeout.sleep(2)
        except BaseException as e:
            message = 'NO EVENTS WERE TRIGGERED FOR: ' + str(self.event_waiting)
            if len(self.event_unkown) > 0:
                message += '\n UNKOWN EVENTS: ' + str(self.event_unkown)

            # FIXME Events triggered in another transaction
            # don't have the transactionHash we are looking for here
            # so we just check if the number of unknown events we find
            # is the same as the found events
            waiting_events = 0
            for ev in list(self.event_waiting.keys()):
                waiting_events += len(list(self.event_waiting[ev].keys()))

            if waiting_events == len(self.event_unkown):
                print('----------------------------------')
                print(message)
                print('----------------------------------')
            else:
                raise Exception(message + ' waiting_events ' + str(waiting_events),
                                ' len(self.event_unkown) ' + str(len(self.event_unkown)))


class LogFilter:
    def __init__(self,
                 web3,
                 abi,
                 address,
                 event_name,
                 from_block=0,
                 to_block='latest',
                 filters=None,
                 callback=None):
        self.web3 = web3
        self.event_name = event_name

        # Callback for every registered log
        self.callback = callback

        filter_kwargs = {
            'fromBlock': from_block,
            'toBlock': to_block,
            'address': address
        }

        event_abi = [i for i in abi if i['type'] == 'event' and i['name'] == event_name]
        if len(event_abi) == 0:
            return None

        self.event_abi = event_abi[0]
        assert self.event_abi

        filters = filters if filters else {}

        data_filter_set, filter_params = construct_event_filter_params(
            self.event_abi,
            argument_filters=filters,
            **filter_kwargs
        )
        log_data_extract_fn = functools.partial(get_event_data, event_abi)

        self.filter = web3.eth.filter(filter_params)
        self.filter.set_data_filters(data_filter_set)
        self.filter.log_entry_formatter = log_data_extract_fn
        self.filter.filter_params = filter_params

    def init(self, post_callback=None):
        for log in self.get_logs():
            log['event'] = self.event_name
            self.callback(log)
        if post_callback:
            post_callback()

    def get_logs(self):
        logs = self.web3.eth.getFilterLogs(self.filter.filter_id)
        formatted_logs = []
        for log in [dict(log) for log in logs]:
            formatted_logs.append(self.set_log_data(log))
        return formatted_logs

    def set_log_data(self, log):
        log['args'] = get_event_data(self.event_abi, log)['args']
        log['event'] = self.event_name
        return log

    def uninstall(self):
        assert self.web3 is not None
        assert self.filter is not None
        self.web3.eth.uninstallFilter(self.filter.filter_id)
        self.filter = None
