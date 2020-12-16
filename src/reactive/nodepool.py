import subprocess

import charms.reactive as reactive
import charms.reactive.relations as relations

import charmhelpers.core as ch_core
import charmhelpers.core.templating as templating
import charmhelpers.core.hookenv as hookenv
# from charmhelpers.core.hookenv import log
from charms import nodepool


@reactive.when('apt.installed.python3-pip')
@reactive.when_not('nodepool.installed')
def install_nodepool():
    subprocess.check_call(['/usr/bin/pip3', 'install', 'nodepool'])
    reactive.set_flag('nodepool.installed')


@reactive.when('nodepool.installed')
@reactive.when_not('endpoint.zookeeper.joined')
def connect_zookeeper():
    hookenv.status_set('blocked', 'Relate Zookeeper to continue')


@reactive.when('nodepool.installed', 'endpoint.zookeeper.joined')
@reactive.when_not('endpoint.zookeeper.available')
def wait_for_zookeeper():
    hookenv.status_set('waiting', 'Waiting for Zookeeper to become available')


@reactive.when_any('config.changed.username',
                   'config.changed.password',
                   'endpoint.zookeeper.changed')
def update_creds():
    reactive.clear_flag('charm.openstack.creds.set')
    reactive.clear_flag('nodepool.configured')


@reactive.when_not('charm.openstack.creds.set')
def get_creds():
    reactive.toggle_flag('charm.openstack.creds.set',
                         nodepool.get_credentials())


@reactive.when('nodepool.installed',
               'endpoint.zookeeper.available',
               'nodepool.cloud.configured',
               'nodepool.user.created')
@reactive.when_not('nodepool.configured')
def configure():
    zookeeper = relations.endpoint_from_flag('endpoint.zookeeper.available')
    conf = {
        'zk_servers': [],
        'nodepool_config': hookenv.config().get('nodepool_config')
    }
    for zk_unit in zookeeper.list_unit_data():
        conf['zk_servers'].append({
            'host': zk_unit['host'].replace('"', ''),
            'port': zk_unit['port']
        })
    templating.render(
        'nodepool.yaml', '/etc/nodepool/nodepool.yaml',
        context=conf, perms=0o650, group='nodepool', owner='nodepool')
    reactive.set_flag('service.nodepool.restart')
    reactive.set_flag('nodepool.configured')


@reactive.when('charm.openstack.creds.set',
               'nodepool.user.created')
@reactive.when_not('nodepool.cloud.configured')
def configure_nodepool_cloud():
    conf = nodepool.get_user_credentials()
    templating.render(
        'clouds.yaml', '/var/lib/nodepool/.config/openstack/clouds.yaml',
        context=conf, perms=0o650, group='nodepool', owner='nodepool')
    reactive.set_flag('nodepool.cloud.configured')


@reactive.when('service.nodepool.restart')
def restart_services():
    ch_core.host.service_restart('nodepool')
    reactive.clear_flag('service.nodepool.restart')


@reactive.when_not('nodepool.user.created')
def add_nodepool_user():
    subprocess.check_call(["groupadd", "--system", "nodepool"])
    subprocess.check_call([
        'useradd', '--system', 'nodepool',
        '--home-dir', '/var/lib/nodepool', '--create-home',
        '-g', 'nodepool'])
    reactive.set_flag('nodepool.user.created')


@reactive.when('nodepool.configured', 'nodepool.user.created')
@reactive.when_not('nodepool.started')
def enable_nodepool():
    templating.render(
        'nodepool.service', '/etc/systemd/system/nodepool.service',
        context={})
    ch_core.host.service_resume('nodepool')
    reactive.set_flag('nodepool.started')


@reactive.when('nodepool.started')
def set_ready():
    hookenv.status_set('active', 'nodepool is ready')
