#!/usr/bin/env python3
#
# Download all versions of an S3 object.

import boto3
import argparse
from argparse import ArgumentParser,SUPPRESS,RawTextHelpFormatter
import time
import re
import os
from tqdm import tqdm

def listVersions(s3bucket, s3prefix):
    # Create empty dict to return data.
    object_dict = {}

    # Build a boto3 resource. 
    s3 = boto3.resource('s3')
    s3bucket = s3.Bucket(s3bucket)
    versions = list(s3bucket.object_versions.filter(Prefix=s3prefix))

    # Iterate over the objects, getting VersionID and LastModified attributes.
    print("Fetching object versions...")
    for version in tqdm(versions, unit=""):
        object = version.get()
        VersionId = object.get('VersionId')
        LastModified = str(object.get('LastModified'))
        object_dict.update({VersionId : LastModified})
    return object_dict

def downloadVersions(s3bucket, s3prefix, output, s3versionId, timestamp):
    # Build a boto3 client. 
    s3 = boto3.client('s3')

    # Massage timestamp into a suitable filename.
    filename = re.sub(r"\s","_",timestamp )

    # Create output directory.
    if not os.path.exists(output):
        os.makedirs(output)
    
    # Download file versions from S3.
    s3.download_file(s3bucket, s3prefix, output+"/"+filename, ExtraArgs={'VersionId': s3versionId})

def UserInput(): 

    s = '''Download all versions of an S3 object.
    
    Example Usage:

./s3versiondownload.py s3://ac-infra-tf-state/environments/dev-apn01/terraform.tfstate ./s3

Fetching object versions...
100%|████████████████████████████████████████████████████| 59/59 [00:07<00:00,  8.27/s]
Downloading object versions to /Users/brandons/Code/stro/aws/s3...
100%|██████████████████████████████████████████████████| 59/59 [00:13<00:00,  4.53it/s]
    '''

    parser = argparse.ArgumentParser(description=s, formatter_class=RawTextHelpFormatter, usage=SUPPRESS)
    parser.add_argument('s3path', type=str, help='S3 object path')
    parser.add_argument('output', type=str, help='Output directory')
    args = parser.parse_args()
    return(args)

def main():
    # Set up argument inputs.
    args = UserInput()

    # Use regex capture groups to pull bucket and target location from input.
    s3resourcepath = re.search('s3:\/\/([^\/]+)\/(.+)', args.s3path)
    s3Bucket = s3resourcepath.group(1)
    s3Prefix = s3resourcepath.group(2)

    # Get list of all available versions.
    version_dict = listVersions(s3Bucket, s3Prefix)

    # Get absoute path of output directory.
    output_path = os.path.abspath(args.output)

    print(f"Downloading object versions to {output_path}...")
    for s3versionId, timestamp in tqdm(version_dict.items()):
        downloadVersions(s3Bucket, s3Prefix, args.output, s3versionId, timestamp)

main()