#!/usr/bin/python
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = '''
---
module: mq_user_info
version_added: 0.9.0
short_description: List users of an Amazon MQ broker
description:
  - list users for the specified broker id
  - Pending creations and deletions can be skipped by options
author: FCO (@fotto)
requirements:
  - boto3
  - botocore
options:
  broker_id:
    description:
      - "The ID of the MQ broker to work on"
    type: str
    required: true
  skip_pending_create:
    description:
      - "Will skip pending creates from the result set"
    type: bool
    default: false
  skip_pending_delete:
    description:
      - "Will skip pending deletes from the result set"
    type: bool
    default: false
  as_dict:
    description:
      - "convert result into lookup table by username"
    type: bool
    default: false

extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
'''


EXAMPLES = '''
- name: get all users as list - relying on environment for API credentials
  amazon.aws.mq_user_info:
    broker_id: "aws-mq-broker-id"
    region: "{{ aws_region }}"
  register: result
- name: get users as dict - explicitly specifying all credentials
  amazon.aws.mq_user_info:
    broker_id: "aws-mq-broker-id"
    region: "{{ aws_region }}"
    aws_access_key: "{{ aws_access_key_id }}"
    aws_secret_key: "{{ aws_secret_access_key }}"
    security_token: "{{ aws_session_token }}"
  register: result
- name: get list of users to decide which may need to be deleted
  amazon.aws.mq_user_info:
    broker_id: "aws-mq-broker-id"
    skip_pending_delete: true
    region: "{{ aws_region }}"
- name: get list of users to decide which may need to be created
  amazon.aws.mq_user_info:
    broker_id: "aws-mq-broker-id"
    skip_pending_create: true
    region: "{{ aws_region }}"
'''

RETURN = '''
users:
    type: dict
    returned: success
    description:
    - dict key is username
    - each entry is the record for a user as returned by API
'''

try:
    import botocore
except ImportError as ex:
    # handled by AnsibleAWSModule
    pass

try:
    # use different package reference to make it work in community.aws. original line
    from ansible.module_utils.core import AnsibleAWSModule
except ImportError as ex:
    raise ex


DEFAULTS = {
    'skip_pending_create': False,
    'skip_pending_delete': False,
    'as_dict': True,
    'page_size': 100
}


def get_user_records(conn, module):
    page_size = DEFAULTS['page_size']
    broker_id = module.params['broker_id']
    next_token = ''
    first_query = True
    records = []

    while next_token or first_query:
        response = conn.list_users(
            BrokerId=broker_id,
            MaxResults=page_size,
            NextToken=next_token
        )
        first_query = False
        records += response['Users']
        if 'NextToken' in response:
            next_token = response['NextToken']
        else:
            next_token = None
    #
    return records


def get_user_info(conn, module):
    try:
        response_records = get_user_records(conn, module)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to describe users')
    #
    if not module.params['skip_pending_create'] and not module.params['skip_pending_delete']:
        # we can simply return the sub-object from the response
        records = response_records
    else:
        records = []
        for record in response_records:
            if 'PendingChange' in record:
                if record['PendingChange'] == 'CREATE' and module.params['skip_pending_create']:
                    continue
                if record['PendingChange'] == 'DELETE' and module.params['skip_pending_delete']:
                    continue
            #
            records.append(record)
    #
    if DEFAULTS['as_dict']:
        user_records = {}
        for record in records:
            user_records[record['Username']] = record
        #
        return user_records
    else:
        return records


def main():
    argument_spec = dict(
        broker_id=dict(required=True, type='str'),
        skip_pending_create=dict(required=False, type='bool', default=DEFAULTS['skip_pending_create']),
        skip_pending_delete=dict(required=False, type='bool', default=DEFAULTS['skip_pending_delete']),
        as_dict=dict(required=False, type='bool', default=False),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    connection = module.client('mq')

    try:
        user_records = get_user_info(connection, module)
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e)

    module.exit_json(users=user_records)


if __name__ == '__main__':
    main()
