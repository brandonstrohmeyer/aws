#!/usr/bin/env python
# check_rtb_size.py

metadata_url = 'http://169.254.169.254/latest/dynamic/instance-identity/document'

import boto3
import requests
import argparse


def arguments():
    parser = argparse.ArgumentParser(description='Returns number of prefixes in specified route '
                                                 'table')
    parser.add_argument('rtb',
                        action='store',
                        help='Route Table ID')

    args = parser.parse_args()
    return args


def get_metadata(url, data):
    response = requests.get(url=url).json()

    return response[data]


def get_rtb_size(rtb):
    table_length = None

    region = get_metadata(metadata_url, 'region')

    client = boto3.client('ec2', region_name=region)

    response = client.describe_route_tables(
        RouteTableIds=[rtb]
    )

    for route_table in response['RouteTables']:
        table_length = len(route_table['Routes'])

    return table_length


def main():
    args = arguments()

    table_length = get_rtb_size(args.rtb)

    print(table_length)


if __name__ == "__main__":
    main()