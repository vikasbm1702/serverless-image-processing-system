# Serverless Image Processing System

A cloud-based tool for resizing and compressing images using AWS Lambda, S3, and API Gateway.

## Project Overview

This project implements a serverless image processing system that:
- Allows users to upload images to an S3 bucket
- Processes images using AWS Lambda with OpenCV
- Resizes and compresses images according to specified parameters
- Saves processed images back to S3
- Provides an API for image upload and retrieval

## Architecture

```
┌─────────┐     ┌─────────────┐     ┌───────────────┐     ┌─────────────┐
│  Client │────▶│ API Gateway │────▶│ AWS Lambda    │────▶│ S3 Bucket   │
│         │◀────│             │◀────│ (OpenCV)      │◀────│ (Processed) │
└─────────┘     └─────────────┘     └───────────────┘     └─────────────┘
                                           │
                                           ▼
                                     ┌─────────────┐
                                     │ S3 Bucket   │
                                     │ (Original)  │
                                     └─────────────┘
```

## Components

1. **S3 Buckets**:
   - `original-images`: Stores uploaded images
   - `processed-images`: Stores processed images

2. **Lambda Function**:
   - Triggered by S3 uploads or API calls
   - Processes images using OpenCV
   - Configurable for different resize/compression options

3. **API Gateway**:
   - Provides RESTful API endpoints
   - Handles image upload requests
   - Returns processed image URLs

## Setup and Deployment

See the deployment guide for instructions on setting up the AWS resources and deploying the application.

## API Documentation

The API provides the following endpoints:
- `POST /process`: Upload and process an image
- `GET /images/{id}`: Retrieve a processed image

## Evaluation

The system is evaluated based on:
- Processing speed
- API efficiency
- Image quality vs. file size
