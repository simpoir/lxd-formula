# -*- coding: utf-8 -*-
'''
Manage LXD networks.

.. versionadded:: Fluorine

.. note:

    - `pylxd`_ version 2 is required to let this work,
      currently only available via pip.

        To install on Ubuntu:

        $ apt-get install libssl-dev python-pip
        $ pip install -U pylxd

    - you need lxd installed on the minion
      for the init() and version() methods.

    - for the config_get() and config_get() methods
      you need to have lxd-client installed.

.. _pylxd: https://github.com/lxc/pylxd/blob/master/doc/source/installation.rst

:maintainer: René Jochum <rene@jochums.at>
:maturity: new
:depends: python-pylxd
:platform: Linux
'''

# Import python libs
from __future__ import absolute_import, print_function, unicode_literals

# Import salt libs
from salt.exceptions import CommandExecutionError
from salt.exceptions import SaltInvocationError
import salt.ext.six as six

__docformat__ = 'restructuredtext en'

__virtualname__ = 'lxd_network'


def __virtual__():
    '''
    Only load if the lxd module is available in __salt__
    '''
    return __virtualname__ if 'lxd.version' in __salt__ else False


def present(name, description=None, config=None,
            remote_addr=None, cert=None, key=None, verify_cert=True):
    '''
    Creates or updates LXD networks

    name :
        The name of the network to create/update

    description :
        A description string

    config :
        A config dict or None (None = unset).

        Can also be a list:
            [{'key': 'boot.autostart', 'value': 1},
             {'key': 'security.privileged', 'value': '1'}]

    remote_addr :
        An URL to a remote Server, you also have to give cert and key if you
        provide remote_addr!

        Examples:
            https://myserver.lan:8443
            /var/lib/mysocket.sock

    cert :
        PEM Formatted SSL Zertifikate.

        Examples:
            ~/.config/lxc/client.crt

    key :
        PEM Formatted SSL Key.

        Examples:
            ~/.config/lxc/client.key

    verify_cert : True
        Wherever to verify the cert, this is by default True
        but in the most cases you want to set it off as LXD
        normaly uses self-signed certificates.

    See the `lxd-docs`_ for the details about the config dict.
    See the `requests-docs` for the SSL stuff.

    .. _lxd-docs: https://github.com/lxc/lxd/blob/master/doc/rest-api.md#post-10
    .. _requests-docs: http://docs.python-requests.org/en/master/user/advanced/#ssl-cert-verification  # noqa
    '''
    ret = {
        'name': name,
        'description': description,
        'config': config,

        'remote_addr': remote_addr,
        'cert': cert,
        'key': key,
        'verify_cert': verify_cert,

        'changes': {}
    }

    network = None
    try:
        network = __salt__['lxd.network_get'](
            name, remote_addr, cert, key, verify_cert, _raw=True
        )
    except CommandExecutionError as e:
        return _error(ret, six.text_type(e))
    except SaltInvocationError as e:
        # Network not found
        pass

    if description is None:
        description = six.text_type()

    if network is None:
        if __opts__['test']:
            # Test is on, just return that we would create the network
            msg = 'Would create the network "{0}"'.format(name)
            ret['changes'] = {'created': msg}
            return _unchanged(ret, msg)

        # Create the network
        try:
            __salt__['lxd.network_create'](
                name,
                config,
                description,
                remote_addr,
                cert,
                key,
                verify_cert
            )

        except CommandExecutionError as e:
            return _error(ret, six.text_type(e))

        msg = 'Network "{0}" has been created'.format(name)
        ret['changes'] = {'created': msg}
        return _success(ret, msg)

    #
    # Description change
    #
    if six.text_type(network.description) != six.text_type(description):
        ret['changes']['description'] = (
            'Description changed, from "{0}" to "{1}".'
        ).format(network.description, description)

        network.description = description

    changes = __salt__['lxd.sync_config_devices'](
        network, config, None, __opts__['test']
    )
    ret['changes'].update(changes)

    if not ret['changes']:
        return _success(ret, 'No changes')

    if __opts__['test']:
        return _unchanged(
            ret,
            'Network "{0}" would get changed.'.format(name)
        )

    try:
        __salt__['lxd.pylxd_save_object'](network)
    except CommandExecutionError as e:
        return _error(ret, six.text_type(e))

    return _success(ret, '{0} changes'.format(len(ret['changes'].keys())))


def absent(name, remote_addr=None, cert=None,
           key=None, verify_cert=True):
    '''
    Ensure a LXD network is not present, removing it if present.

    name :
        The name of the network to remove.

    remote_addr :
        An URL to a remote Server, you also have to give cert and key if you
        provide remote_addr!

        Examples:
            https://myserver.lan:8443
            /var/lib/mysocket.sock

    cert :
        PEM Formatted SSL Zertifikate.

        Examples:
            ~/.config/lxc/client.crt

    key :
        PEM Formatted SSL Key.

        Examples:
            ~/.config/lxc/client.key

    verify_cert : True
        Wherever to verify the cert, this is by default True
        but in the most cases you want to set it off as LXD
        normaly uses self-signed certificates.

    See the `requests-docs` for the SSL stuff.

    .. _requests-docs: http://docs.python-requests.org/en/master/user/advanced/#ssl-cert-verification  # noqa
    '''
    ret = {
        'name': name,

        'remote_addr': remote_addr,
        'cert': cert,
        'key': key,
        'verify_cert': verify_cert,

        'changes': {}
    }
    if __opts__['test']:
        try:
            __salt__['lxd.network_get'](
                name, remote_addr, cert, key, verify_cert
            )
        except CommandExecutionError as e:
            return _error(ret, six.text_type(e))
        except SaltInvocationError as e:
            # Network not found
            return _success(ret, 'Network "{0}" not found.'.format(name))

        ret['changes'] = {
            'removed':
            'Network "{0}" would get deleted.'.format(name)
        }
        return _success(ret, ret['changes']['removed'])

    try:
        __salt__['lxd.network_delete'](
            name, remote_addr, cert, key, verify_cert
        )
    except CommandExecutionError as e:
        return _error(ret, six.text_type(e))
    except SaltInvocationError as e:
        # Network not found
        return _success(ret, 'Network "{0}" not found.'.format(name))

    ret['changes'] = {
        'removed':
        'Network "{0}" has been deleted.'.format(name)
    }
    return _success(ret, ret['changes']['removed'])


def _success(ret, success_msg):
    ret['result'] = True
    ret['comment'] = success_msg
    if 'changes' not in ret:
        ret['changes'] = {}
    return ret


def _unchanged(ret, msg):
    ret['result'] = None
    ret['comment'] = msg
    if 'changes' not in ret:
        ret['changes'] = {}
    return ret


def _error(ret, err_msg):
    ret['result'] = False
    ret['comment'] = err_msg
    if 'changes' not in ret:
        ret['changes'] = {}
    return ret
