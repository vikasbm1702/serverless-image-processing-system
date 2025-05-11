#!/usr/bin/env python3
"""
Simplified script to set up S3 buckets for the Serverless Image Processing System.
This creates only the S3 buckets, as the user doesn't have permissions for IAM and Lambda.
"""

import boto3
import os
import time
import random
from dotenv import load_dotenv

load_dotenv()

# Generate a unique suffix for bucket names
timestamp = int(time.time())
random_suffix = random.randint(1000, 9999)
unique_suffix = f"{timestamp}-{random_suffix}"

# Configuration
PROJECT_NAME = "serverless-image-processor"
REGION = os.getenv("AWS_REGION", "eu-north-1")  # Using the region you configured
ORIGINAL_BUCKET = f"{PROJECT_NAME}-original-{unique_suffix}"
PROCESSED_BUCKET = f"{PROJECT_NAME}-processed-{unique_suffix}"

print(f"Using unique bucket names with suffix: {unique_suffix}")
print(f"Original bucket: {ORIGINAL_BUCKET}")
print(f"Processed bucket: {PROCESSED_BUCKET}")

# Initialize AWS client
s3_client = boto3.client('s3', region_name=REGION)

def create_s3_buckets():
    """Create S3 buckets for original and processed images."""
    print("Creating S3 buckets...")

    # Create bucket for original images
    try:
        s3_client.create_bucket(
            Bucket=ORIGINAL_BUCKET,
            CreateBucketConfiguration={'LocationConstraint': REGION}
        )
        print(f"Created bucket: {ORIGINAL_BUCKET}")
    except Exception as e:
        print(f"Error creating bucket {ORIGINAL_BUCKET}: {e}")

    # Create bucket for processed images
    try:
        s3_client.create_bucket(
            Bucket=PROCESSED_BUCKET,
            CreateBucketConfiguration={'LocationConstraint': REGION}
        )
        print(f"Created bucket: {PROCESSED_BUCKET}")
    except Exception as e:
        print(f"Error creating bucket {PROCESSED_BUCKET}: {e}")

    # Configure CORS for the original bucket to allow uploads from browser
    cors_configuration = {
        'CORSRules': [{
            'AllowedHeaders': ['*'],
            'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE', 'HEAD'],
            'AllowedOrigins': ['*'],
            'ExposeHeaders': []
        }]
    }

    try:
        s3_client.put_bucket_cors(Bucket=ORIGINAL_BUCKET, CORSConfiguration=cors_configuration)
        print(f"Configured CORS for bucket: {ORIGINAL_BUCKET}")
    except Exception as e:
        print(f"Error configuring CORS for bucket {ORIGINAL_BUCKET}: {e}")

def main():
    """Main function to set up S3 buckets."""
    print("Setting up S3 buckets for Serverless Image Processing System...")

    # Create S3 buckets
    create_s3_buckets()

    print("\nS3 buckets setup complete!")
    print(f"Original Images Bucket: {ORIGINAL_BUCKET}")
    print(f"Processed Images Bucket: {PROCESSED_BUCKET}")

    print("\nNext steps:")
    print("1. Create a Lambda function in the AWS Console")
    print("2. Upload the lambda_deployment_package.zip file")
    print("3. Set environment variables in the Lambda function:")
    print(f"   - ORIGINAL_BUCKET={ORIGINAL_BUCKET}")
    print(f"   - PROCESSED_BUCKET={PROCESSED_BUCKET}")
    print("4. Create an API Gateway trigger for the Lambda function")

    # Save configuration to .env file
    with open('.env', 'w') as f:
        f.write(f"AWS_REGION={REGION}\n")
        f.write(f"ORIGINAL_BUCKET={ORIGINAL_BUCKET}\n")
        f.write(f"PROCESSED_BUCKET={PROCESSED_BUCKET}\n")

    print("\nConfiguration saved to .env file")

    # Update client config.js with the new bucket names
    try:
        config_path = os.path.join('client', 'config.js')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config_content = f.read()

            # Replace bucket names
            config_content = config_content.replace(
                "originalBucket: 'serverless-image-processor-original'",
                f"originalBucket: '{ORIGINAL_BUCKET}'"
            )
            config_content = config_content.replace(
                "processedBucket: 'serverless-image-processor-processed'",
                f"processedBucket: '{PROCESSED_BUCKET}'"
            )

            with open(config_path, 'w') as f:
                f.write(config_content)

            print(f"Updated client configuration in {config_path}")
        else:
            print(f"Warning: Client config file {config_path} not found")
    except Exception as e:
        print(f"Error updating client config: {e}")

if __name__ == "__main__":
    main()
