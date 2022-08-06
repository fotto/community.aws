#!/usr/bin/python
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = '''
---
module: mq_user_info
<<<<<<< HEAD
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
=======
version_added: 4.1.0
short_description: List users of an Amazon MQ broker
description:
  - List users for the specified broker ID.
  - Pending creations and deletions can be skipped by options.
author:
  - FCO (@fotto)
options:
  broker_id:
    description:
      - The ID of the MQ broker to work on.
>>>>>>> 4b5a4eb47689b7250c566e93ef5dcdadc1a89c98
    type: str
    required: true
  max_results:
    description:
<<<<<<< HEAD
      - "The maximum number of results to return"
=======
      - The maximum number of results to return.
>>>>>>> 4b5a4eb47689b7250c566e93ef5dcdadc1a89c98
    type: int
    default: 100
  skip_pending_create:
    description:
<<<<<<< HEAD
      - "Will skip pending creates from the result set"
=======
      - Will skip pending creates from the result set.
>>>>>>> 4b5a4eb47689b7250c566e93ef5dcdadc1a89c98
    type: bool
    default: false
  skip_pending_delete:
    description:
<<<<<<< HEAD
      - "Will skip pending deletes from the result set"
=======
      - Will skip pending deletes from the result set.
>>>>>>> 4b5a4eb47689b7250c566e93ef5dcdadc1a89c98
    type: bool
    default: false
  as_dict:
    description:
<<<<<<< HEAD
      - "convert result into lookup table by username"
=======
      - Convert result into lookup table by username.
>>>>>>> 4b5a4eb47689b7250c566e93ef5dcdadc1a89c98
    type: bool
    default: false

extends_documentation_fragment:
<<<<<<< HEAD
- amazon.aws.aws
- amazon.aws.ec2
=======
  - amazon.aws.aws
  - amazon.aws.ec2
>>>>>>> 4b5a4eb47689b7250c566e93ef5dcdadc1a89c98
'''


EXAMPLES = '''
- name: get all users as list - relying on environment for API credentials
  amazon.aws.mq_user_info:
    broker_id: "aws-mq-broker-id"
    max_results: 50
<<<<<<< HEAD
    region: "{{ aws_region }}"
=======
>>>>>>> 4b5a4eb47689b7250c566e93ef5dcdadc1a89c98
  register: result
- name: get users as dict - explicitly specifying all credentials
  amazon.aws.mq_user_info:
    broker_id: "aws-mq-broker-id"
<<<<<<< HEAD
    region: "{{ aws_region }}"
    aws_access_key: "{{ aws_access_key_id }}"
    aws_secret_key: "{{ aws_secret_access_key }}"
    security_token: "{{ aws_session_token }}"
=======
>>>>>>> 4b5a4eb47689b7250c566e93ef5dcdadc1a89c98
  register: result
- name: get list of users to decide which may need to be deleted
  amazon.aws.mq_user_info:
    broker_id: "aws-mq-broker-id"
    skip_pending_delete: true
<<<<<<< HEAD
    region: "{{ aws_region }}"
=======
>>>>>>> 4b5a4eb47689b7250c566e93ef5dcdadc1a89c98
- name: get list of users to decide which may need to be created
  amazon.aws.mq_user_info:
    broker_id: "aws-mq-broker-id"
    skip_pending_create: true
<<<<<<< HEAD
    region: "{{ aws_region }}"
=======
>>>>>>> 4b5a4eb47689b7250c566e93ef5dcdadc1a89c98
'''

RETURN = '''
users:
    type: dict
    returned: success
    description:
<<<<<<< HEAD
    - dict key is username
    - each entry is the record for a user as returned by API
=======
      - dict key is username
      - each entry is the record for a user as returned by API
>>>>>>> 4b5a4eb47689b7250c566e93ef5dcdadc1a89c98
'''

try:
    import botocore
except ImportError as ex:
    # handled by AnsibleAWSModule
    pass

<<<<<<< HEAD
try:
    # use different package reference to make it work in community.aws. original line
    # from ansible.module_utils.core import AnsibleAWSModule
    from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
except ImportError as ex:
    raise ex
=======
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
>>>>>>> 4b5a4eb47689b7250c566e93ef5dcdadc1a89c98


DEFAULTS = {
    'max_results': 100,
    'skip_pending_create': False,
    'skip_pending_delete': False,
    'as_dict': True
}


def get_user_info(conn, module):
    try:
        response = conn.list_users(BrokerId=module.params['broker_id'],
                                   MaxResults=module.params['max_results'])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        if module.check_mode:
            # return empty set for unknown broker in check mode
            if DEFAULTS['as_dict']:
                return {}
            else:
                return []
        else:
            module.fail_json_aws(e, msg='Failed to describe users')
    #
    if not module.params['skip_pending_create'] and not module.params['skip_pending_delete']:
        # we can simply return the sub-object from the response
        records = response['Users']
    else:
        records = []
        for record in response['Users']:
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
        max_results=dict(required=False, type='int', default=DEFAULTS['max_results']),
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
