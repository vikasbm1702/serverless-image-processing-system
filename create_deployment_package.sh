#!/bin/bash
# Script to create a deployment package for AWS Lambda

# Create a directory for the package
echo "Creating deployment package directory..."
mkdir -p lambda_package

# Install dependencies into the package directory
echo "Installing dependencies..."
pip install -r requirements.txt -t lambda_package

# Copy the Lambda function code
echo "Copying Lambda function code..."
cp lambda_function.py lambda_package/

# Create the deployment package
echo "Creating deployment package zip file..."
cd lambda_package
zip -r ../lambda_deployment_package.zip .
cd ..

echo "Deployment package created: lambda_deployment_package.zip"
echo "You can now upload this package to AWS Lambda."
