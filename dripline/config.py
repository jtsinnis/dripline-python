""" config.py

This module contains the definition of the Config class.  The Config class
is the in-memory representation of the configuration of a dripline node.

"""

from __future__ import with_statement
from yaml import safe_load

import logging
LOGGER = logging.getLogger(__name__)
STREAM_HANDLER = logging.StreamHandler()
MSG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
FORMATTER = logging.Formatter(MSG_FORMAT)
ch.setFormatter(FORMATTER)
logger.setLevel(logging.INFO)
logger.addHandler(STREAM_HANDLER)


class Config(object):
    """
    The Config class contains all of the configuration data that is relevant
    to a dripline node, and is in fact how a dripline object graph is created.
    An instance of Config is created from a YAML string which describes a
    hierarchical graph of objects.  Each object has a unique name, and has zero
    or more descendents which form a tree-like structure.  The node level object
    may have descendents which are Providers (see provider.py) or Endpoints
    (see endpoint.py), and Providers may have descendents which are Endpoints.

    The Config object is responsible for the run-time checking of the YAML
    document which describes the dripline node configuration.  The rules which
    are checked are straightforward:

    * Names within categories must be unique - no two providers may have the
        same name, and no two endpoints may have the same name.

    * No object may have a name which contains a period.

    * Every object must be constructable.  This means that there is a
        module or function which can be called by dripline at runtime to handle
        requests which are addressed to that object.

    With these considerations in mind, the following YAML description of a
    dripline node is acceptable:

        nodename: example
        broker: foo.bar.baz
        providers:
        - name: provider0
          module: a_provider_module
          endpoints:
          - name: endpoint0
            module: an_endpoint_module
          - name: endpoint1
            module: another_endpoint_module
        - name: provider1
          module: a_provider_module
          endpoints:
          - name: endpoint2
            module: an_endpoint_module
          - name: endpoint3
            module: yet_another_endpoint_module

    For further examples of configuration files, see the configuration.yaml
    file in the examples directory.
    # TODO configuration.yaml file a la rebar.config demo file.
    """

    def __init__(self, config_file=None):
        """
        Construct a Config instance with its configuration data based on the
        content of the YAML file specified in config_file.  If the configuration
        data is invalid, various exceptions may be raised:

        * In the case of duplicate names at the provider or endpoint level, a
        ValueError will be raised with a description of the duplication.

        * If any names contain periods, a ValueError will be raised with a
        description of the offending datum.

        If __init__ succeeds, the resulting Config object may be used to
        instantiate a Node object.

        Note: Config has no association with the network whatsoever.  It does
        not check that e.g. there is an AMQP server available at the address
        specified in the YAML configuration file.  Therefore, while the
        connectivity of the graph is guaranteed by the Config class, the
        correct network configuration cannot be verified until a Node is
        constructed.
        """
        self.nodename = None
        self.broker = None
        self.instruments = {}
        if config_file is not None:
            try:
                with open(config_file) as config:
                    self._from_yaml(config.read())
            except IOError, err:
                msg = """
                couldn't open config file {} (io error occurred: {})
                """.format(config_file, err.message)
                LOGGER.error(msg)
                raise err

    def instrument_count(self):
        """
        Returns the number of providers which are associated with the node,
        exclusive of the node itself.  This means that for a configuration file
        which contains no providers, provider_count will return zero.
        """
        return len(self.instruments.keys())

    def get_provider(self, provider_name):
        """
        Return the data associated with a given provider.
        """
        return self[provider_name]

    def _from_yaml(self, yaml_string):
        """
        Generates a dictionary of objects and their relationships from a
        YAML configuration file.  If the configuration file is invalid for
        any reason, an exception is thrown.
        """
        rep = safe_load(yaml_string)
        self.nodename = rep['nodename']
        self.broker = rep['broker']
        if 'instruments' in rep:
            for instrument in rep['instruments']:
                instr_name = instrument.pop('name')
                if self.instruments.has_key(instr_name):
                    msg = """
                    duplicate definition: provider with name {} already defined!
                    (origin provider: {}/{})
                    """.format(instr_name, self.nodename, instr_name)
                    raise ValueError(msg)

                # TODO repeat the check inside the provider to catch duplicate
                # endpoint names.
                self.instruments[instr_name] = instrument
        else:
            self.instruments = None
