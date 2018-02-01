#!/usr/bin/python
#
# Python 2.7
#
# AWS EIP Collector v1.2
#
# Collects list of EIPs assigned in AWS and outputs CSV file.
# Requires awscli and aws-mfa for initial authentication.

# Pre-existing ./aws/config profile with read access to organization
org_profile = 'example-master'

# IAM role allowed to cross role switch into each account.
cross_account_role = 'CrossAccountSignInExample'

### End of Configuration ###

import boto3
import time
import csv
from collections import OrderedDict
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

def list_account(org):
    # Get list of accounts in org

    print 'Looking for accounts in organization...'
    account_list = []
    session = boto3.Session(profile_name=org)
    client = session.client('organizations')
    response = client.list_accounts(
        MaxResults=10
    )
    while 'NextToken' in response:
        for account in response['Accounts']:
            account_list.append(account['Id'])

        response = client.list_accounts(
            MaxResults=10,
            NextToken=response['NextToken']
        )
    print '  %s accounts found' % (len(account_list))
    print ''
    return account_list

def list_eip(account, role):
    # Get a list of all allocated EIPs in account for all regions

    region_list = []
    eip_dict = defaultdict(dict)

    # Get list of all regions for ec2 service
    ec2_client = boto3.client('ec2')
    response = ec2_client.describe_regions()
    for region in response['Regions']:
        region_list.append(region['RegionName'])

    for region in region_list:
        #S et credentials for cross role account switching
        sts_client = boto3.client('sts')
        assumedRoleObject = sts_client.assume_role(
            RoleArn='arn:aws:iam::%s:role/%s' % (account, role),
            RoleSessionName='AssumeRoleSession1'
        )

        credentials = assumedRoleObject['Credentials']
        ec2_client = boto3.client('ec2',
                                  aws_access_key_id=credentials['AccessKeyId'],
                                  aws_secret_access_key=credentials['SecretAccessKey'],
                                  aws_session_token=credentials['SessionToken'],
                                  region_name=region
                                  )

        # Get all EIPs for account in all regions
        response = ec2_client.describe_addresses()

        # Build dict with all relevant EIP details
        # Prefer Instance ID, but will settle for ENI ID
        for address in response['Addresses']:
            eip_dict[address['PublicIp']]['eip'] = address['PublicIp']
            eip_dict[address['PublicIp']]['account'] = account
            eip_dict[address['PublicIp']]['region'] = region
            if 'InstanceId' in address:
                eip_dict[address['PublicIp']]['id'] = address['InstanceId']
            elif 'NetworkInterfaceId' in address:
                eip_dict[address['PublicIp']]['id'] = address['NetworkInterfaceId']
            else:
                eip_dict[address['PublicIp']]['id'] = 'Unassociated'
    return eip_dict

def main():
    start = time.time()
    list_eip_threads = {}
    eip_dict = {}

    account_list = list_account(org_profile)

    # Process 5 accounts at a time
    pool = ThreadPoolExecutor(5)

    for account in account_list:

      # Create future object from jobs submitted to pool
       list_eip_thread = pool.submit(list_eip, account, cross_account_role)

       # Aggregate future objects in dict
       list_eip_threads[account] = list_eip_thread

    # Check on the progress of the futures objects
    kwargs = {
        'total': len(account_list),
        'bar_format':'{l_bar}{bar}| {n_fmt}/{total_fmt} accounts [{elapsed}]   '
    }

    print 'Looking for EIPs...'
    for s in tqdm(as_completed(list_eip_threads.values()), **kwargs):
      pass

    # Call for the result of the future objects
    for account, t in list_eip_threads.items():
        eip_dict[account] = t.result()

    # Clean up eip_dict to remove top level "account" key
    eip_data_dict = OrderedDict()
    for key in eip_dict:
        eip_data_dict.update(OrderedDict((k, v) for k, v in eip_dict[key].iteritems()))
    print 'Done!'
    print ''

    print 'Writing file "eip.csv"...'

    # Get all unique dict keys to be used as CSV header
    fields = set()
    for k1, v1 in eip_data_dict.iteritems():
        for k2, v2 in v1.iteritems():
            fields.add(k2)

    # Write data to csv file in current directory
    with open("eip.csv", "wb") as out_file:
        w = csv.DictWriter(out_file, fields)
        w.writeheader()
        for key in eip_data_dict:
            w.writerow({field: eip_data_dict[key].get(field) for field in fields})

    end = time.time()

    print''
    print'Total Elastic IPs found: %s' % (sum(len(v) for v in eip_dict.itervalues()))
    print'Task duration:', end - start

main()


