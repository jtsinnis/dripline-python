import re

from _dripline.core import Service

__all__ = []

__all__.append('AlertConsumer')
class AlertConsumer(Service):
    '''
    A base class for implementing custom alert message consumers.

    One is expected to extend this class in one of two ways:
    1) More advanced: override the existing on_alert_message method with whatever behavior is desired
    2) Use the existing on_alert_message, which proceeds in two steps by calling parse_routing_key, followed by process_payload.
       The first may be used or overriden, the second must always be implemented.
    '''
    def __init__(self, alert_keys=["#"], alert_key_parser_re='', **kwargs):
        '''
        alert_keys: an iterable of strings which will be used as binding keys on the alerts exchange
        alert_key_parser_re: a regular expression (see python's re library) which is used in the default implementation
                             of parse_routing_key to extract useful data from the incoming routing key.  Note: a failed
                             match will return an empty dict, you are responsible for checkin and deciding if this is an
                             error. We use re.match and return the groupdict.
        '''
        print("in AlertConsumer init")
        Service.__init__(self, **kwargs)
        self._alert_keys = alert_keys
        self._alert_key_parser_re= alert_key_parser_re

    def bind_keys(self):
        print("in python's bind keys")
        to_return = Service.bind_keys(self);
        for a_key in self._alert_keys:
            print(" binding alert key {}".format(a_key))
            to_return = to_return and self.bind_key("alerts", a_key)
        return to_return

    def on_alert_message(self, an_alert):
        print("in python's on alert")
        routing_data = self.parse_routing_key(an_alert.routing_key)
        print("routing key data are:\n{}".format(routing_data))
        self.process_payload(an_alert.payload, routing_data, an_alert.timestamp)

    def parse_routing_key(self, a_routing_key):
        return_data = {}
        print("routing key: '{}'".format(a_routing_key))
        print("regex: '{}'".format(self._alert_key_parser_re))
        re_result = re.match(self._alert_key_parser_re, a_routing_key)
        if re_result:
            return_data.update(re_result.groupdict())
        else:
            print("WARNING!! regular expression match failed to extract any data")
        return return_data

    def process_payload(self, a_payload, a_routing_key_data, a_message_timestamp):
        print('got routing key data: {}\nwith payload: {}'.format(a_routing_key_data, a_payload))
