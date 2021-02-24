#!/usr/bin/python
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = '''
---
module: mq_broker
version_added: 0.9.0
short_description: MQ broker management
description:
  - create/update/delete a broker.
  - reboot a broker
author: FCO (@fotto)
requirements:
  - boto3
  - botocore
options:
  broker_name:
    description:
    - "The Name of the MQ broker to work on"
    type: str
    required: true
  state:
    description:
    - "'present': create/update broker"
    - "'absent': delete broker"
    - "'restarted': reboot broker"
    choices: [ 'present', 'absent', 'restarted' ]
    default: present
    type: str
  deployment_mode:
    description:
    - set broker deployment type
    - can be used only during creation
    - "default: 'SINGLE_INSTANCE'"
    choices: [ 'SINGLE_INSTANCE', 'ACTIVE_STANDBY_MULTI_AZ', 'CLUSTER_MULTI_AZ' ]
    type: str
  use_aws_owned_key:
    description:
    - must be set to false if 'kms_key_id' is provided as well
    - can be used only during creation
    - "default: true"
    type: bool
  kms_key_id:
    description:
    - use referenced key to encrypt broker data at rest
    - can be used only during creation
    type: str
  engine_type:
    description:
    - set broker engine type
    - can be used only during creation
    - "default: 'ACTIVEMQ'"
    choices: [ 'ACTIVEMQ', 'RABBITMQ' ]
    type: str
  maintenance_window_start_time:
    description:
    - set maintenance window for automatic minor upgrades
    - can be used only during creation
    - not providing any value means "no maintenance window"
    type: dict
  publicly_accessible:
    description:
    - allow/disallow public access
    - can be used only during creation
    - "default: false"
    type: bool
  storage_type:
    description:
    - set underlying storage type
    - can be used only during creation
    - "default: 'EFS'"
    choices: [ 'EBS', 'EFS' ]
    type: str
  subnet_ids:
    description:
    - defines where deploy broker instances to
    - minimum required number depends on deployment type
    - can be used only during creation
    type: list
    elements: str
  users:
    description:
    - "module 'mq_user' is the preferred way to manage (local) users"
    - "however a broker cannot be created without any user"
    - "if nothing is specified a default 'admin' user will be created along with brokers"
    - "this parameter allows to use a custom set of initial user(s)"
    - "can be used only during creation: use mq_user module for updates"
    type: list
    elements: dict
  tags:
    description:
    - tag newly created brokers
    - can be used only during creation
    type: dict
  authentication_strategy:
    description: choose between locally and remotely managed users
    choices: [ 'SIMPLE', 'LDAP' ]
    type: str
  auto_minor_version_upgrade:
    description: allow/disallow automatic minor version upgrades
    type: bool
    default: true
  engine_version:
    description: set engine version of broker
    type: str
  host_instance_type:
    description: instance type of broker instances
    type: str
  enable_audit_log:
    description: enable/disable to push audit logs to AWS CloudWatch
    type: bool
    default: false
  enable_general_log:
    description: enable/disable to push general logs to AWS CloudWatch
    type: bool
    default: false
  security_groups:
    description:
    - associate security groups with broker
    - at least one must be provided during creation
    type: list
    elements: str
  region:
    description:
    - set AWS region for API operations
    type: str

extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''


EXAMPLES = '''
- name: create broker (if missing) with minimal required parameters
  amazon.aws.mq_broker:
    broker_name: "{{ broker_name }}"
    region: "{{ aws_region }}"
    security_groups:
    - sg_xxxxxxx
    subnet_ids:
    - subnet_xxx
    - subnet_yyy
    register: result
- set_fact:
    broker_id: "{{ result.broker['BrokerId'] }}"
- name: use mq_broker_info to wait until broker is ready
  amazon.aws.mq_broker_info:
    broker_id: "{{ broker_id }}"
    region: "{{ aws_region }}"
  register: result
  until: "result.broker['BrokerState'] == 'RUNNING'"
  retries: 15
  delay:   60
- name: create or update broker with almost all parameter set including credentials
  amazon.aws.mq_broker:
    broker_name: "my_broker_2"
    state: present
    deployment_mode: 'ACTIVE_STANDBY_MULTI_AZ'
    use_aws_owned_key: false
    kms_key_id: 'my-precreted-key-id'
    engine_type: 'ACTIVEMQ'
    maintenance_window_start_time:
      DayOfWeek: 'MONDAY'
      TimeOfDay: '03:15'
      TimeZone: 'Europe/Berlin'
    publicly_accessible: true
    storage_type: 'EFS'
    security_groups:
    - sg_xxxxxxx
    subnet_ids:
    - subnet_xxx
    - subnet_yyy
    region: "{{ aws_region }}"
    aws_access_key: "{{ aws_access_key_id }}"
    aws_secret_key: "{{ aws_secret_access_key }}"
    security_token: "{{ aws_session_token }}"
    users:
    - Username: 'initial-user'
      Password': 'plain-text-password'
      ConsoleAccess: true
    tags:
    - env: Test
      creator: ansible
    authentication_strategy: 'SIMPLE'
    auto_minor_version_upgrade: true
    engine_version: "5.15.13"
    host_instance_type: 'mq.t3.micro'
    enable_audit_log: true
    enable_general_log: true
- name: reboot a broker
  amazon.aws.mq_broker:
    broker_name: "my_broker_2"
    state: restarted
    region: "{{ aws_region }}"
- name: delete a broker
  amazon.aws.mq_broker:
    broker_name: "my_broker_2"
    state: absent
    region: "{{ aws_region }}"
'''

RETURN = '''
broker:
    description:
    - "'state=present': API response of create_broker() or update_broker() call"
    - "'state=absent': result of describe_broker() call before delete_broker() is triggerd"
    - "'state=restarted': result of describe_broker() after reboot has been triggered"
    type: dict
    returned: success
'''

try:
    import botocore
except ImportError as ex:
    # handled by AnsibleAWSModule
    pass

try:
    # when moving to amazon.aws change import to
    # from ansible.module_utils.core import AnsibleAWSModule
    from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
except ImportError as ex:
    raise ex


PARAMS_MAP = {
    'authentication_strategy': 'AuthenticationStrategy',
    'auto_minor_version_upgrade': 'AutoMinorVersionUpgrade',
    'broker_name': 'BrokerName',
    'deployment_mode': 'DeploymentMode',
    'use_aws_owned_key': 'EncryptionOptions/UseAwsOwnedKey',
    'kms_key_id': 'EncryptionOptions/KmsKeyId',
    'engine_type': 'EngineType',
    'engine_version': 'EngineVersion',
    'host_instance_type': 'HostInstanceType',
    'enable_audit_log': 'Logs/Audit',
    'enable_general_log': 'Logs/General',
    'maintenance_window_start_time': 'MaintenanceWindowStartTime',
    'publicly_accessible': 'PubliclyAccessible',
    'security_groups': 'SecurityGroups',
    'storage_type': 'StorageType',
    'subnet_ids': 'SubnetIds',
    'users': 'Users'
}


DEFAULTS = {
    'authentication_strategy': 'SIMPLE',
    'auto_minor_version_upgrade': False,
    'deployment_mode': 'SINGLE_INSTANCE',
    'use_aws_owned_key': True,
    'engine_type': 'ACTIVEMQ',
    'engine_version': '5.15.13',
    'host_instance_type': 'mq.t3.micro',
    'enable_audit_log': False,
    'enable_general_log': False,
    'publicly_accessible': False,
    'storage_type': 'EFS'
}

CREATE_ONLY_PARAMS = [
    'deployment_mode',
    'use_aws_owned_key',
    'kms_key_id',
    'engine_type',
    'maintenance_window_start_time',
    'publicly_accessible',
    'storage_type',
    'subnet_ids',
    'users',
    'tags'
]


def _set_kwarg(kwargs, key, value):
    mapped_key = PARAMS_MAP[key]
    if '/' in mapped_key:
        key_list = mapped_key.split('/')
        key_list.reverse()
    else:
        key_list = [mapped_key]
    data = kwargs
    while len(key_list) > 1:
        this_key = key_list.pop()
        if this_key not in data:
            data[this_key] = {}
        #
        data = data[this_key]
    data[key_list[0]] = value


def _fill_kwargs(module, apply_defaults=True, ignore_create_params=False):
    kwargs = {}
    if apply_defaults:
        for p_name in DEFAULTS:
            _set_kwarg(kwargs, p_name, DEFAULTS[p_name])
    for p_name in module.params:
        if ignore_create_params and p_name in CREATE_ONLY_PARAMS:
            # silently ignore CREATE_ONLY_PARAMS on updated to
            # make playbooks idempotent
            continue
        if p_name in PARAMS_MAP and module.params[p_name] is not None:
            _set_kwarg(kwargs, p_name, module.params[p_name])
        else:
            # ignore
            pass
    return kwargs


def get_broker_id(conn, module):
    try:
        broker_name = module.params['broker_name']
        broker_id = None
        response = conn.list_brokers(MaxResults=100)
        for broker in response['BrokerSummaries']:
            if broker['BrokerName'] == broker_name:
                broker_id = broker['BrokerId']
                break
        return broker_id
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't list broker brokers.")


def get_broker_info(conn, module, broker_id):
    try:
        return conn.describe_broker(BrokerId=broker_id)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't get broker details.")


def reboot_broker(conn, module, broker_id):
    try:
        return conn.reboot_broker(
            BrokerId=broker_id
        )
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't reboot broker.")


def delete_broker(conn, module, broker_id):
    try:
        return conn.delete_broker(
            BrokerId=broker_id
        )
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't delete broker.")


def create_broker(conn, module):
    kwargs = _fill_kwargs(module)
    if kwargs['AuthenticationStrategy'] == 'LDAP':
        module.fail_json_aws(RuntimeError, msg="'AuthenticationStrategy=LDAP' not supported, yet")
    if 'Users' not in kwargs:
        # add some stupid default (cannot create broker without any users)
        kwargs['Users'] = [
            {
                'Username': 'admin',
                'Password': 'adminPassword',
                'ConsoleAccess': True,
                'Groups': []
            }
        ]
    if 'EncryptionOptions' in kwargs and 'UseAwsOwnedKey' in kwargs['EncryptionOptions']:
        kwargs['EncryptionOptions']['UseAwsOwnedKey'] = False
    #
    if 'SecurityGroups' not in kwargs or len(kwargs['SecurityGroups']) == 0:
        module.fail_json_aws(RuntimeError, msg="At least one security group must be specified on broker creation")
    #
    changed = True
    if not module.check_mode:
        result = conn.create_broker(**kwargs)
    else:
        result = {
            'BrokerArn': 'fakeArn',
            'BrokerId': 'fakeId'
        }
    #
    return {'broker': result, 'changed': changed}


def update_broker(conn, module, broker_id):
    kwargs = _fill_kwargs(module, apply_defaults=False, ignore_create_params=True)
    # replace name with id
    del kwargs['BrokerName']
    kwargs['BrokerId'] = broker_id
    # TODO: get current state and check whether change is necessary at all
    changed = True
    if not module.check_mode:
        result = conn.update_broker(**kwargs)
    else:
        result = {
            'BrokerId': broker_id
        }
    #
    return {'broker': result, 'changed': changed}


def ensure_present(conn, module):
    broker_id = get_broker_id(conn, module)
    if broker_id:
        return update_broker(conn, module, broker_id)
    else:
        return create_broker(conn, module)


def main():
    argument_spec = dict(
        broker_name=dict(required=True, type='str'),
        state=dict(default='present', choices=['present', 'absent', 'restarted']),
        # parameters only allowed on create
        deployment_mode=dict(choices=['SINGLE_INSTANCE', 'ACTIVE_STANDBY_MULTI_AZ', 'CLUSTER_MULTI_AZ']),
        use_aws_owned_key=dict(type='bool'),
        kms_key_id=dict(type='str'),
        engine_type=dict(choices=['ACTIVEMQ', 'RABBITMQ'], type='str'),
        maintenance_window_start_time=dict(type='dict'),
        publicly_accessible=dict(type='bool'),
        storage_type=dict(choices=['EBS', 'EFS']),
        subnet_ids=dict(type='list', elements='str'),
        users=dict(type='list', elements='dict'),
        tags=dict(type='dict'),
        # parameters allowed on update as well
        authentication_strategy=dict(choices=['SIMPLE', 'LDAP']),
        auto_minor_version_upgrade=dict(default=True, type='bool'),
        engine_version=dict(type='str'),
        host_instance_type=dict(type='str'),
        enable_audit_log=dict(default=False, type='bool'),
        enable_general_log=dict(default=False, type='bool'),
        security_groups=dict(type='list', elements='str')
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    connection = module.client('mq')

    if module.params['state'] == 'present':
        try:
            compound_result = ensure_present(connection, module)
        except botocore.exceptions.ClientError as e:
            module.fail_json_aws(e)
        #
        module.exit_json(**compound_result)
    elif module.params['state'] == 'absent':
        broker_id = get_broker_id(connection, module)
        if not broker_id:
            module.fail_json_aws(RuntimeError,
                                 msg="Cannot find broker with name {0}.".format(module.params['broker_name']))
        result = get_broker_info(connection, module, broker_id)
        try:
            changed = True
            if not module.check_mode:
                delete_broker(connection, module, broker_id)
        except botocore.exceptions.ClientError as e:
            module.fail_json_aws(e)
        #
        module.exit_json(broker=result, changed=changed)
    elif module.params['state'] == 'restarted':
        broker_id = get_broker_id(connection, module)
        if not broker_id:
            module.fail_json_aws(RuntimeError,
                                 msg="Cannot find broker with name {0}.".format(module.params['broker_name']))
        try:
            changed = True
            if not module.check_mode:
                reboot_broker(connection, module, broker_id)
            #
            result = get_broker_info(connection, module, broker_id)
        except botocore.exceptions.ClientError as e:
            module.fail_json_aws(e)
        module.exit_json(broker=result, changed=changed)
    else:
        module.fail_json_aws(RuntimeError,
                             msg="Invalid broker state requested ({0}). Valid are: 'present', 'absent', 'restarted'".format(module.params['state']))


if __name__ == '__main__':
    main()