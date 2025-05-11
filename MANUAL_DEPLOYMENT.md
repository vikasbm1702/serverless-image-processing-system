# Manual Deployment Guide for Serverless Image Processing System

Since we encountered permission issues with the automated deployment script, here's a guide for manually deploying the system using the AWS Console.

## Prerequisites

1. AWS account with access to:
   - S3
   - Lambda
   - API Gateway

2. The S3 buckets have already been created:
   - Original images: `serverless-image-processor-original-images`
   - Processed images: `serverless-image-processor-processed-images`

3. Lambda deployment package: `lambda_deployment_package.zip`

## Step 1: Create the Lambda Function

1. Go to the [AWS Lambda Console](https://console.aws.amazon.com/lambda)
2. Click "Create function"
3. Select "Author from scratch"
4. Enter function details:
   - Name: `serverless-image-processor-function`
   - Runtime: Python 3.9
   - Architecture: x86_64
5. Click "Create function"
6. In the "Code" tab:
   - Click "Upload from" and select ".zip file"
   - Upload the `lambda_deployment_package.zip` file
   - Click "Save"
7. In the "Configuration" tab:
   - Click "Environment variables"
   - Add the following variables:
     - Key: `ORIGINAL_BUCKET`, Value: `serverless-image-processor-original-images`
     - Key: `PROCESSED_BUCKET`, Value: `serverless-image-processor-processed-images`
   - Click "Save"
   - Click "General configuration"
   - Set Timeout to 30 seconds
   - Set Memory to 512 MB
   - Click "Save"

## Step 2: Configure Lambda Permissions

1. In the Lambda function page, go to the "Configuration" tab
2. Click "Permissions"
3. Click on the role name under "Execution role"
4. In the IAM console, click "Add permissions" and then "Attach policies"
5. Search for and attach the following policies:
   - `AmazonS3FullAccess`
   - `AWSLambdaBasicExecutionRole`
6. Click "Attach policies"

## Step 3: Create API Gateway

1. Go to the [API Gateway Console](https://console.aws.amazon.com/apigateway)
2. Click "Create API"
3. Select "REST API" and click "Build"
4. Select "New API" and enter:
   - API name: `serverless-image-processor-api`
   - Description: API for Serverless Image Processing
5. Click "Create API"
6. Click "Actions" and select "Create Resource"
7. Enter "process" as the Resource Name and click "Create Resource"
8. With the new resource selected, click "Actions" and select "Create Method"
9. Select "POST" from the dropdown and click the checkmark
10. Configure the POST method:
    - Integration type: Lambda Function
    - Lambda Region: eu-north-1 (or your region)
    - Lambda Function: serverless-image-processor-function
11. Click "Save"
12. Click "Actions" and select "Enable CORS"
13. Check all the options and click "Enable CORS and replace existing CORS headers"
14. Click "Actions" and select "Deploy API"
15. Create a new stage named "prod" and click "Deploy"
16. Note the "Invoke URL" at the top of the stage editor page

## Step 4: Update the Client Application

1. Open the `client/index.html` file
2. Replace the API_URL value with your actual API Gateway URL:
   ```javascript
   const API_URL = 'https://YOUR_API_ID.execute-api.eu-north-1.amazonaws.com/prod/process';
   ```
   Replace `YOUR_API_ID` with the actual API ID from the Invoke URL.

## Step 5: Test the System

1. Host the client application locally:
   ```bash
   cd client
   python -m http.server 8000
   ```
2. Open a web browser and navigate to `http://localhost:8000`
3. Upload an image, set processing parameters, and click "Process Image"
4. Verify that the image is processed and the results are displayed

## Troubleshooting

If you encounter issues:

1. Check the Lambda function logs in CloudWatch
2. Verify that the Lambda function has the correct permissions
3. Make sure the API Gateway is properly configured
4. Check that the environment variables are set correctly in the Lambda function
