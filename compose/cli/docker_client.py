from __future__ import absolute_import
from __future__ import unicode_literals

import logging

from ..common.const import HTTP_TIMEOUT
from ..core import dockerclient as dc
from .errors import UserError

log = logging.getLogger(__name__)


def tls_config_from_options(options):
    tls = options.get('--tls', False)
    ca_cert = options.get('--tlscacert')
    cert = options.get('--tlscert')
    key = options.get('--tlskey')
    verify = options.get('--tlsverify')
    skip_hostname_check = options.get('--skip-hostname-check', False)

    advanced_opts = any([ca_cert, cert, key, verify])

    if tls is True and not advanced_opts:
        return True
    elif advanced_opts:  # --tls is a noop
        client_cert = None
        if cert or key:
            client_cert = (cert, key)

        return dc.tls.TLSConfig(
            client_cert=client_cert, verify=verify, ca_cert=ca_cert,
            assert_hostname=False if skip_hostname_check else None
        )

    return None


def docker_client(environment, version=None, tls_config=None, host=None):
    """
    Returns a docker-py client configured using environment variables
    according to the same logic as the official Docker client.
    """
    if 'DOCKER_CLIENT_TIMEOUT' in environment:
        log.warn("The DOCKER_CLIENT_TIMEOUT environment variable is deprecated.  "
                 "Please use COMPOSE_HTTP_TIMEOUT instead.")

    try:
        kwargs = dc.utils.kwargs_from_env(environment=environment)
    except dc.errors.TLSParameterError:
        raise UserError(
            "TLS configuration is invalid - make sure your DOCKER_TLS_VERIFY "
            "and DOCKER_CERT_PATH are set correctly.\n"
            "You might need to run `eval \"$(docker-machine env default)\"`")

    if host:
        kwargs['base_url'] = host
    if tls_config:
        kwargs['tls'] = tls_config

    if version:
        kwargs['version'] = version

    timeout = environment.get('COMPOSE_HTTP_TIMEOUT')
    if timeout:
        kwargs['timeout'] = int(timeout)
    else:
        kwargs['timeout'] = HTTP_TIMEOUT

    return dc.client.Client(**kwargs)
