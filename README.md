# cloneEC2.py
Python script that automates EC2 cloning process, optionally replaces source parameters when launching new instance.

## Setup with Virtual Environment
```
# clone the repository
git https://github.com/edmondsiu0/cloneEC2.git
cd cloneEC2

# enable virtual environment
python3 -m venv venv
source venv/bin/activate

# install required modules into virtual environment
pip3 install -r requirements.txt
```

## Usage

### Basic Usage
```
# python3 cloneEC2.py <region> <source_ec2_instance_id>
```
This command will perform the following actions:
1. Create an AMI from source_ec2_instance_id, wait till new AMI become available.
2. Retrieve configuration of source_ec2_instance_id.
3. Launch a new EC2 instance using new AMI (from 1) and configuration retrieved (from 2).

### Advanced Usage
```
# python3 cloneEC2.py <region> <source_ec2_instance_id> <key1=value1> <key2=value2>...
```
Configuration retrieved from the source_ec2_instance_id can be replaced by providing key=value pairs through command line arguments.

The following parameters can be overridden using this key=value pair method:
* `ImageId`
* `InstanceType`
* `KeyName`
* `SubnetId`

**NOTE**: If `ImageId` is specified, the script will skip AMI creation and uses AMI ID supplied, and launch a new instance using configuration from source_ec2_instance_id.

## Examples

#### To clone an EC2 instance, and launch using same parameters as source instance:
```
# python3 cloneEC2.py eu-west-1 i-0123456789abcdef0
```

#### To clone an EC2 instance like above, but place new instance in subnet-0123456789abcdef0:
```
# python3 cloneEC2.py eu-west-1 i-0123456789abcdef0 SubnetId=subnet-0123456789abcdef0
```

#### To clone an EC2 instance like above, but place new in subnet-0123456789abcdef0, and change Instance Type to 't3.small':
```
# python3 cloneEC2.py eu-west-1 i-0123456789abcdef0 SubnetId=subnet-0123456789abcdef0 InstanceType=t3.small
```

#### To launch an EC2 instance using parameters from i-0123456789abcdef0, and existing ami-0123456789abcdef0:
```
# python3 cloneEC2.py eu-west-1 i-0123456789abcdef0 ImageId=ami-0123456789abcdef0
```
