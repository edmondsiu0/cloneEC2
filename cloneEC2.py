# cloneEC2.py
# Created: 17th June 2021
# Last modified: 2nd Sept 2021
#
# Automatically creates an AMI (with reboot) from EC2 instance, then launches the new AMI using parameters from the source EC2 instance.
# Optionally, override instance parameters by specifying key=value pairs in the command line.
#
# Basic Usage:
# python3 cloneEC2.py <region> <source_ec2_instance_id>
#
# Advanced Usage:
# python3 cloneEC2.py <region> <source_ec2_instance_id> <key1=value1> <key2=value2>...
#
#
# The following <key=value> parameter pairs can be supplied to override configurations used to launch the new instance:
#
#  * ImageId - if supplied script will not capture AMI from source EC2 instance.
#  * InstanceType
#  * KeyName
#  * SubnetId
#
# (See examples below.)
#
#
# Examples:
#  1. To clone an EC2 instance, automatically create new AMI from source EC2 instance, then launch using same parameters as source instance:
#     python3 cloneEC2.py eu-west-1 i-0123456789abcdef0
#
#  2. To clone an EC2 instance like above, but place new instance in subnet-0123456789abcdef0:
#     python3 cloneEC2.py eu-west-1 i-0123456789abcdef0 SubnetId=subnet-0123456789abcdef0
#
#  3. To clone an EC2 instance like above, but place new in subnet-0123456789abcdef0, and change Instance Type to 't3.small':
#     python3 cloneEC2.py eu-west-1 i-0123456789abcdef0 SubnetId=subnet-0123456789abcdef0 InstanceType=t3.small
#
#  4. To launch an EC2 instance using parameters from i-0123456789abcdef0, and existing ami-0123456789abcdef0:
#     python3 cloneEC2.py eu-west-1 i-0123456789abcdef0 ImageId=ami-0123456789abcdef0
#
#

import boto3
import string
import random
import time
import sys

# Defining global variables shared across all functions
global region
global sourceinstance
global sysargv_config


def create_image(instanceid):
    # Passes input to boto3 create_image function, returns Image ID as string.
    client = boto3.client('ec2', region_name=region)

    # Generating a random string
    letters = string.ascii_lowercase

    response = client.create_image(
        InstanceId=instanceid,
        Name=instanceid + '-' + ''.join(random.choice(letters) for i in range(10))
    )

    imageid=response['ImageId']
    return(imageid)


def image_status(ami):
    # Passes input to boto3 describe_images function, returns Image State as string.
    client = boto3.client('ec2', region_name=region)
    response = client.describe_images(
        ImageIds=[ami]
    )

    state = response['Images'][0]['State']
    return(state)


def get_instance_config(instanceid):
    # Passes input to boto3 describe_instances, return instance configuration as dictionary.
    client = boto3.client('ec2', region_name=region)
    response = client.describe_instances(
        InstanceIds=[instanceid]
    )

    source_config = response['Reservations'][0]['Instances'][0]
    return(source_config)


def sanitise_instance_config(source_config):
    # Operate on input dictionary obtained from get_instance_config,
    # sanitise SecurityGroups and IamInstanceProfile to format ingestible by boto3 run_instances,
    # filter source config to the list of parameters described in filter_keys list.
    # Return sanitised config as dictionary.

    # Sanitising SecurityGroups and removing key value elements not required by run_instances
    security_groups_list = []

    security_groups = source_config['SecurityGroups']
    for sg in security_groups:
        security_groups_list.append(sg['GroupId'])

    source_config['SecurityGroups'] = security_groups_list

    # Parameters to be retained
    filter_keys = [
        'ImageId',
        'InstanceType',
        'KeyName',
        'SubnetId',
        'VpcId',
        'SecurityGroups',
        'IamInstanceProfile',
        'EbsOptimized',
        'Tags'
    ]

    # Sanitising IamInstanceProfile and removing key value pairs not required by run_instances
    if 'IamInstanceProfile' in source_config:
        source_config['IamInstanceProfile'] = source_config['IamInstanceProfile']['Arn']
    else:
        source_config['IamInstanceProfile'] = ''

    meta_tags = [
        {
            'Key': 'CloneMethod',
            'Value': 'cloneEC2.py'
        },
        {
            'Key': 'CloneSource',
            'Value': sourceinstance
        }
    ]

    if 'Tags' in source_config:
        source_tags = source_config['Tags']
        source_config['Tags'] = meta_tags
        for tag in source_tags:
            if not tag['Key'].startswith('aws:'):
                 source_config['Tags'].append(tag)
    else:
        source_config['Tags'] = meta_tags

    # Sanitising input config
    filtered_config = {}

    for key in filter_keys:
        filtered_config[key] = source_config[key]

    return(filtered_config)


def modify_instance_config(source_config, **kwargs):
    # Merging and overwriting input dictionary with matching input **kwargs, return merged config as dictionary.
    append_config = {}

    for key, value in kwargs.items():
        append_config[key] = value

    new_config = {**source_config, **append_config}

    return(new_config)

def run_instance(config):
    # Passes input to boto3 run_instances, return Instance ID as string.
    client = boto3.client('ec2', region_name=region)

    response = client.run_instances(
        ImageId             = config['ImageId'],
        InstanceType        = config['InstanceType'],
        KeyName             = config['KeyName'],
        SubnetId            = config['SubnetId'],
        SecurityGroupIds    = config['SecurityGroups'],
        EbsOptimized        = config['EbsOptimized'],
        IamInstanceProfile  = {
            'Arn': config['IamInstanceProfile']
        },
        TagSpecifications   = [
            {
                'ResourceType': 'instance',
                'Tags': config['Tags']
            }
        ],
        MinCount = 1,
        MaxCount = 1
    )

    instanceid = response['Instances'][0]['InstanceId']

    return(instanceid)


def main():

    if 'ImageId' not in sysargv_config:
        print('\n=> ImageId not specified, creating an AMI from EC2 instance (' + sourceinstance + ')')

        ami = create_image(sourceinstance)

        print('\n<= Waiting for (' + ami + ') to become available...')

        while (image_status(ami) != 'available'):
            time.sleep(5)
            print('...Still waiting for AMI to become available...')
            time.sleep(5)


        print('\n<= Image (' + ami + ') status: ' + image_status(ami))
    else:
        ami = sysargv_config['ImageId']
        print('\n<= ImageID specified, using (' + ami + ') to launch new instance.')


    print('\n<= Getting source EC2 configuration (' + sourceinstance + ')...')
    source_config = get_instance_config(sourceinstance)

    print('\n<= Sanitised source EC2 configuration:')
    sanitised_source_config = sanitise_instance_config(source_config)
    print(sanitised_source_config)

    print('\n<= Modified EC2 configuration:')
    custom_config = {'ImageId':ami, **sysargv_config}
    new_config = modify_instance_config(sanitised_source_config, **custom_config)
    print(new_config)

    print('\n=> Launching new EC2 instance...')
    instanceid = run_instance(new_config)
    print('\n<= New EC2 Insatnce ID: ' + instanceid + '\n')

if __name__ == "__main__":
    # Checking for sys.argv length and assign variables from system command line input.
    if len(sys.argv) < 3:
        raise SyntaxError("Insufficient arguments, expected arguments: <region> <source ec2 instance id> <key=value>...")
    if len(sys.argv) > 3:
        region = sys.argv[1]
        sourceinstance = sys.argv[2]
        sysargv_config = dict(arg.split('=') for arg in sys.argv[3:])
    if len(sys.argv) == 3:
        region = sys.argv[1]
        sourceinstance = sys.argv[2]
        sysargv_config = {}
    main()
