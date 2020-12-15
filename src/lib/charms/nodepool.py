import subprocess

import yaml

from charmhelpers.core import hookenv
from charmhelpers.core.unitdata import kv


def log(msg, *args):
    hookenv.log(msg.format(*args), hookenv.INFO)


def log_err(msg, *args):
    hookenv.log(msg.format(*args), hookenv.ERROR)


def get_credentials():
    """
    Get the credentials from either the config or the hook tool.

    Prefers the config so that it can be overridden.
    """
    config = hookenv.config()

    # try individual config
    if any([config['auth-url'],
            config['username'],
            config['password'],
            config['project-name'],
            config['user-domain-name'],
            config['project-domain-name'],
            config['region-name'],
            config['cloud-name']]):
        log('Using individual config values for credentials')
        _save_creds(config)
        return True

    # try to use Juju's trust feature
    try:
        result = subprocess.run(['credential-get'],
                                check=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        creds_data = yaml.load(result.stdout.decode('utf8'))

        log('Using credentials-get for credentials')
        _save_creds(creds_data)
        return True
    except FileNotFoundError:
        pass  # juju trust not available
    except subprocess.CalledProcessError as e:
        if 'permission denied' not in e.stderr.decode('utf8'):
            raise
        no_creds_msg = 'missing credentials access; grant with: juju trust'
        # no creds provided
        hookenv.status_set('blocked', no_creds_msg)
    return False


def get_user_credentials():
    return _load_creds()


def cleanup():
    pass

# Internal helpers


def _save_creds(creds_data):
    if 'endpoint' in creds_data:
        endpoint = creds_data['endpoint']
        attrs = creds_data['credential']['attributes']
    else:
        attrs = creds_data
        endpoint = attrs['auth-url']

    if 'region' in creds_data:
        region = creds_data['region']
    else:
        region = attrs['region-name']
    if 'name' in creds_data:
        cloud_name = creds_data['name']
    else:
        cloud_name = attrs['cloud-name']

    if 'ca-certificates' in creds_data:
        # see K8s commit e3c8a0ceb66816433b095c4d734663e1b1e0e4ea
        # K8s in-tree cloud provider code is not flexible enough
        # to accept multiple certs that could be provided by Juju
        # so we can grab the first one only and hope it is the
        # right one
        ca_certificates = creds_data.get('ca-certificates')
        ca_cert = ca_certificates[0] if ca_certificates else None
    elif 'endpoint-tls-ca' in creds_data:
        ca_cert = creds_data['endpoint-tls-ca']
    else:
        ca_cert = None

    kv().set('charm.openstack.full-creds', dict(
        auth_url=endpoint,
        username=attrs['username'],
        password=attrs['password'],
        user_domain_name=attrs['user-domain-name'],
        project_domain_name=attrs['project-domain-name'],
        project_name=attrs.get('project-name', attrs.get('tenant-name')),
        region_name=region,
        cloud_name=cloud_name,
        endpoint_tls_ca=ca_cert,
    ))


def _load_creds():
    return kv().get('charm.openstack.full-creds')
