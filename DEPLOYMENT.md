# Deployment Guide: Serverless Image Processing System

This guide will walk you through deploying the Serverless Image Processing System to AWS.

## Prerequisites

1. **AWS Account**: You need an AWS account with appropriate permissions to create and manage the following services:
   - AWS Lambda
   - Amazon S3
   - AWS IAM
   - Amazon API Gateway

2. **AWS CLI**: Install and configure the AWS Command Line Interface.
   ```bash
   pip install awscli
   aws configure
   ```

3. **Python 3.9+**: Ensure you have Python 3.9 or later installed.

4. **Required Python Packages**: Install the required packages.
   ```bash
   pip install -r requirements.txt
   ```

## Deployment Steps

### 1. Set Up AWS Credentials

Ensure your AWS credentials are properly configured:

```bash
aws configure
```

You'll need to provide:
- AWS Access Key ID
- AWS Secret Access Key
- Default region name (e.g., us-east-1)
- Default output format (json)

### 2. Create AWS Resources

Run the setup script to create all necessary AWS resources:

```bash
python setup_aws_resources.py
```

This script will:
- Create S3 buckets for original and processed images
- Create an IAM role for the Lambda function
- Create and deploy the Lambda function
- Set up API Gateway
- Configure S3 event triggers

The script will output the URLs and resource names that you'll need for the next steps.

### 3. Update the Client Application

Open the `client/index.html` file and update the API URL:

```javascript
// Replace with your actual API URL from the AWS deployment
const API_URL = 'YOUR_API_GATEWAY_URL';
```

Replace `'YOUR_API_GATEWAY_URL'` with the API URL output from the setup script.

### 4. Test the Deployment

#### Test the Lambda Function

You can test the Lambda function directly in the AWS Console:

1. Go to the AWS Lambda Console
2. Select your function (`serverless-image-processor-function`)
3. Create a test event with the following JSON:

```json
{
  "body": "{\"image\":\"data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAIBAQIBAQICAgICAgICAwUDAwMDAwYEBAMFBwYHBwcGBwcICQsJCAgKCAcHCg0KCgsMDAwMBwkODw0MDgsMDAz/2wBDAQICAgMDAwYDAwYMCAcIDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAz/wAARCAABAAEDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD9/KKKKAP/2Q==\",\"width\":800,\"quality\":85}"
}
```

4. Click "Test" and verify the function executes successfully

#### Test the Complete System

1. Host the client application (you can use a simple HTTP server):
   ```bash
   cd client
   python -m http.server 8000
   ```

2. Open a web browser and navigate to `http://localhost:8000`

3. Upload an image, set processing parameters, and click "Process Image"

4. Verify that the image is processed and the results are displayed

## Monitoring and Troubleshooting

### CloudWatch Logs

Lambda automatically logs to CloudWatch. To view logs:

1. Go to the AWS CloudWatch Console
2. Select "Log groups"
3. Find the log group for your Lambda function (`/aws/lambda/serverless-image-processor-function`)

### Common Issues

1. **Lambda Timeout**: If processing large images, you might need to increase the Lambda timeout and memory allocation.

2. **CORS Issues**: If you're getting CORS errors when calling the API from the browser, ensure the API Gateway has CORS enabled.

3. **Permission Issues**: Ensure the Lambda function has the correct permissions to access S3 buckets.

## Cleaning Up

To avoid incurring charges, delete the resources when you're done:

```bash
aws s3 rb s3://serverless-image-processor-original-images --force
aws s3 rb s3://serverless-image-processor-processed-images --force
aws lambda delete-function --function-name serverless-image-processor-function
aws iam detach-role-policy --role-name serverless-image-processor-lambda-role --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
aws iam detach-role-policy --role-name serverless-image-processor-lambda-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam delete-role --role-name serverless-image-processor-lambda-role
aws apigateway delete-rest-api --rest-api-id YOUR_API_ID
```

Replace `YOUR_API_ID` with the actual API ID from the setup script output.

## Next Steps

- Add authentication to the API
- Implement additional image processing features
- Set up a CloudFront distribution for the client application
- Add monitoring and alerting for the system
