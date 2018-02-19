from web3.utils.filters import construct_event_filter_params
import functools
from web3.utils.events import get_event_data


class LogFilter:
    def __init__(
        self,
        web3,
        abi,
        address,
        event_name,
        from_block=0,
        to_block='latest',
        filters=None,
        callback=None
    ):
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
