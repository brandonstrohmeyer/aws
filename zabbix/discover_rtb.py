#!/usr/bin/env python
# discover_rtb.py

metadata_url = 'http://169.254.169.254/latest/dynamic/instance-identity/document'

import boto3
import json
import requests


def get_metadata(url, data):
    response = requests.get(url=url).json()

    return response[data]


def get_vpc_id(instance_id):
    region = get_metadata(metadata_url, 'region')

    client = boto3.client('ec2', region_name=region)

    response = client.describe_instances(
        InstanceIds=[
            instance_id
        ]
    )

    return response['Reservations'][0]['Instances'][0]['VpcId']


def describe_route_tables():
    rtb_list = []
    json_output = {}
    region = get_metadata(metadata_url, 'region')
    instance_id = get_metadata(metadata_url, 'instanceId')
    vpc_id = get_vpc_id(instance_id)

    client = boto3.client('ec2', region_name=region)

    response = client.describe_route_tables(
        Filters=[
            {
                'Name': 'vpc-id',
                'Values': [
                    vpc_id
                ]
            }
        ]
    )

    for route_table in response['RouteTables']:
        rtb_dict = {}

        rtb_dict['{#RTBID}'] = route_table['RouteTableId']

        rtb_list.append(rtb_dict)

    json_output['data'] = rtb_list

    return json.dumps(json_output, indent=4)


def main():
    route_tables = describe_route_tables()

    print route_tables


if __name__ == "__main__":
    main()