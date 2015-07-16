'''
Basic abstraction for binding to the alerts exchange
'''

from __future__ import absolute_import

# standard libs
import logging
import traceback
import uuid

# 3rd party libs
import pika

# internal imports
from .message import Message
from .service import Service

__all__ = ['AlertConsumer']

logger = logging.getLogger(__name__)


class AlertConsumer(Service):
    def __init__(self, broker_host='localhost', exchange='alerts', keys=['#'], name=None): 
        '''
        Keyword Args:
            broker_host (str): network address of the amqp broker to connect to
            exchange (str): AMQP exchange on the broker to which we will be binding
            keys (list): list of strings, each string will be a routing key bound to the provided exchange.

        '''
        logger.debug('AlertConsumer initializing')
        if name is None:
            name = __name__ + '-' + uuid.uuid1().hex[:12]
        Service.__init__(self, amqp_url=broker_host, exchange=exchange, keys=keys, name=name)

    def this_consume(self, message):
        raise NotImplementedError('you must set this_consume to a valid function')

    @staticmethod
    def _print_consume(message):
        logger.debug('using default message consumption')
        logger.info('{}'.format(message))
    def _postgres_consume(self, message):
        data = {}
        for key in ['value_raw', 'value_cal', 'memo']:
            try:
                data[key] = message['payload']['values'][key]
            except:
                pass

        insert_dict = {'endpoint_name': message['payload']['from'],
                       'timestamp': message['timestamp'],
                      }
        insert_dict.update(data)
        try:
            ins = self.table.insert().values(**insert_dict)
            ins.execute()
        except Exception as err:
            if 'no known endpoint with name' in err.message:
                logger.critical("Unable to log for <{}>, sensor not in SQL table".format(err.message.split('with name')[-1]))
                return
            if 'sqlalchemny' in repr(err):
                logger.critical("got an unknown sqlalchemy error: {}".format(repr(err)))
                return
            if 'psycopg2' in repr(err):
                logger.critical("got an unknown psycopg2 error: {}".format(repr(err)))
                return
            else:
                logger.warning('unknown error during sqlalchemy insert:\n{}'.format(err))
                raise

    def on_message(self, channel, method, properties, message):
        logger.debug('in process_message callback')
        try:
            message_unpacked = Message.from_encoded(message, properties.content_encoding)
            self.this_consume(message_unpacked)
        except Exception as err:
            logger.warning('got an exception (trying to continue running):\n{}'.format(err.message))
            logger.debug('traceback follows:\n{}'.format(traceback.format_exc()))
            raise

    def start(self):
        logger.debug("AlertConsmer consume starting")
        self.run()
#        self.dripline_connection.chan.basic_consume(process_message,
#                                                    queue=self.queue.method.queue,
#                                                    no_ack=True
#                                                   )
#        self.dripline_connection.chan.start_consuming()
