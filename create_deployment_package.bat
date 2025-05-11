@echo off
REM Script to create a deployment package for AWS Lambda on Windows

echo Creating deployment package directory...
if not exist lambda_package mkdir lambda_package

echo Installing dependencies...
pip install -r requirements.txt -t lambda_package

echo Copying Lambda function code...
copy lambda_function.py lambda_package\

echo Creating deployment package zip file...
cd lambda_package
powershell Compress-Archive -Path * -DestinationPath ..\lambda_deployment_package.zip -Force
cd ..

echo Deployment package created: lambda_deployment_package.zip
echo You can now upload this package to AWS Lambda.
