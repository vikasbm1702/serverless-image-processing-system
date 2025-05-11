#!/usr/bin/env python3
"""
Script to set up AWS resources for the Serverless Image Processing System.
This creates:
- S3 buckets for original and processed images
- IAM role for Lambda
- Lambda function
- API Gateway
"""

import boto3
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
PROJECT_NAME = "serverless-image-processor"
REGION = os.getenv("AWS_REGION", "us-east-1")
ORIGINAL_BUCKET = f"{PROJECT_NAME}-original-images"
PROCESSED_BUCKET = f"{PROJECT_NAME}-processed-images"
LAMBDA_FUNCTION_NAME = f"{PROJECT_NAME}-function"
LAMBDA_ROLE_NAME = f"{PROJECT_NAME}-lambda-role"
API_NAME = f"{PROJECT_NAME}-api"

# Initialize AWS clients
s3_client = boto3.client('s3', region_name=REGION)
lambda_client = boto3.client('lambda', region_name=REGION)
iam_client = boto3.client('iam', region_name=REGION)
apigateway_client = boto3.client('apigateway', region_name=REGION)

def create_s3_buckets():
    """Create S3 buckets for original and processed images."""
    print("Creating S3 buckets...")
    
    # Create bucket for original images
    try:
        s3_client.create_bucket(Bucket=ORIGINAL_BUCKET)
        print(f"Created bucket: {ORIGINAL_BUCKET}")
    except Exception as e:
        print(f"Error creating bucket {ORIGINAL_BUCKET}: {e}")
    
    # Create bucket for processed images
    try:
        s3_client.create_bucket(Bucket=PROCESSED_BUCKET)
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

def create_lambda_role():
    """Create IAM role for Lambda function."""
    print("Creating IAM role for Lambda...")
    
    # Define trust relationship policy
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    # Create the role
    try:
        response = iam_client.create_role(
            RoleName=LAMBDA_ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Role for Serverless Image Processing Lambda function"
        )
        role_arn = response['Role']['Arn']
        print(f"Created IAM role: {LAMBDA_ROLE_NAME}")
        
        # Attach policies
        iam_client.attach_role_policy(
            RoleName=LAMBDA_ROLE_NAME,
            PolicyArn="arn:aws:iam::aws:policy/AmazonS3FullAccess"
        )
        iam_client.attach_role_policy(
            RoleName=LAMBDA_ROLE_NAME,
            PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        )
        print("Attached policies to IAM role")
        
        # Wait for role to propagate
        print("Waiting for role to propagate...")
        time.sleep(10)
        
        return role_arn
    except Exception as e:
        print(f"Error creating IAM role: {e}")
        return None

def create_lambda_function(role_arn):
    """Create Lambda function for image processing."""
    print("Creating Lambda function...")
    
    # First, create a deployment package
    os.system("pip install -r requirements.txt -t ./lambda_package")
    os.system("cp lambda_function.py ./lambda_package/")
    os.system("cd lambda_package && zip -r ../lambda_deployment_package.zip .")
    
    # Create the Lambda function
    try:
        with open('lambda_deployment_package.zip', 'rb') as f:
            zipped_code = f.read()
        
        response = lambda_client.create_function(
            FunctionName=LAMBDA_FUNCTION_NAME,
            Runtime='python3.9',
            Role=role_arn,
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': zipped_code},
            Timeout=30,
            MemorySize=512,
            Environment={
                'Variables': {
                    'ORIGINAL_BUCKET': ORIGINAL_BUCKET,
                    'PROCESSED_BUCKET': PROCESSED_BUCKET
                }
            }
        )
        
        function_arn = response['FunctionArn']
        print(f"Created Lambda function: {LAMBDA_FUNCTION_NAME}")
        
        # Configure S3 to trigger Lambda
        s3_client.put_bucket_notification_configuration(
            Bucket=ORIGINAL_BUCKET,
            NotificationConfiguration={
                'LambdaFunctionConfigurations': [
                    {
                        'LambdaFunctionArn': function_arn,
                        'Events': ['s3:ObjectCreated:*']
                    }
                ]
            }
        )
        print(f"Configured S3 trigger for Lambda function")
        
        return function_arn
    except Exception as e:
        print(f"Error creating Lambda function: {e}")
        return None

def create_api_gateway(lambda_arn):
    """Create API Gateway to trigger Lambda function."""
    print("Creating API Gateway...")
    
    try:
        # Create API
        api_response = apigateway_client.create_rest_api(
            name=API_NAME,
            description='API for Serverless Image Processing',
            endpointConfiguration={'types': ['REGIONAL']}
        )
        api_id = api_response['id']
        
        # Get root resource id
        resources = apigateway_client.get_resources(restApiId=api_id)
        root_id = [resource['id'] for resource in resources['items'] if resource['path'] == '/'][0]
        
        # Create resource
        resource_response = apigateway_client.create_resource(
            restApiId=api_id,
            parentId=root_id,
            pathPart='process'
        )
        resource_id = resource_response['id']
        
        # Create POST method
        apigateway_client.put_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='POST',
            authorizationType='NONE',
            apiKeyRequired=False
        )
        
        # Set Lambda integration
        apigateway_client.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='POST',
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=f'arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
        )
        
        # Deploy API
        apigateway_client.create_deployment(
            restApiId=api_id,
            stageName='prod'
        )
        
        # Grant API Gateway permission to invoke Lambda
        lambda_client.add_permission(
            FunctionName=LAMBDA_FUNCTION_NAME,
            StatementId='apigateway-invoke',
            Action='lambda:InvokeFunction',
            Principal='apigateway.amazonaws.com',
            SourceArn=f'arn:aws:execute-api:{REGION}:*:{api_id}/*/*'
        )
        
        api_url = f'https://{api_id}.execute-api.{REGION}.amazonaws.com/prod/process'
        print(f"Created API Gateway: {API_NAME}")
        print(f"API URL: {api_url}")
        
        return api_url
    except Exception as e:
        print(f"Error creating API Gateway: {e}")
        return None

def main():
    """Main function to set up all AWS resources."""
    print("Setting up AWS resources for Serverless Image Processing System...")
    
    # Create S3 buckets
    create_s3_buckets()
    
    # Create IAM role for Lambda
    role_arn = create_lambda_role()
    if not role_arn:
        print("Failed to create IAM role. Exiting.")
        return
    
    # Create Lambda function
    lambda_arn = create_lambda_function(role_arn)
    if not lambda_arn:
        print("Failed to create Lambda function. Exiting.")
        return
    
    # Create API Gateway
    api_url = create_api_gateway(lambda_arn)
    if not api_url:
        print("Failed to create API Gateway. Exiting.")
        return
    
    print("\nAWS resources setup complete!")
    print(f"Original Images Bucket: {ORIGINAL_BUCKET}")
    print(f"Processed Images Bucket: {PROCESSED_BUCKET}")
    print(f"Lambda Function: {LAMBDA_FUNCTION_NAME}")
    print(f"API URL: {api_url}")
    
    # Save configuration to .env file
    with open('.env', 'w') as f:
        f.write(f"AWS_REGION={REGION}\n")
        f.write(f"ORIGINAL_BUCKET={ORIGINAL_BUCKET}\n")
        f.write(f"PROCESSED_BUCKET={PROCESSED_BUCKET}\n")
        f.write(f"LAMBDA_FUNCTION_NAME={LAMBDA_FUNCTION_NAME}\n")
        f.write(f"API_URL={api_url}\n")
    
    print("Configuration saved to .env file")

if __name__ == "__main__":
    main()
