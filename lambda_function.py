import json
import os
import boto3
import cv2
import numpy as np
from PIL import Image
import io
import uuid
import base64
import urllib.parse

# Initialize S3 client
s3_client = boto3.client('s3')

# Get environment variables
ORIGINAL_BUCKET = os.environ.get('ORIGINAL_BUCKET')
PROCESSED_BUCKET = os.environ.get('PROCESSED_BUCKET')

def resize_image(image, width=None, height=None):
    """
    Resize an image while maintaining aspect ratio.
    If both width and height are provided, the image will be resized to fit within those dimensions.
    """
    if width is None and height is None:
        return image

    h, w = image.shape[:2]

    # Calculate new dimensions
    if width and height:
        # Resize to fit within the specified dimensions while maintaining aspect ratio
        aspect = w / h
        if w > h:
            new_w = width
            new_h = int(width / aspect)
            if new_h > height:
                new_h = height
                new_w = int(height * aspect)
        else:
            new_h = height
            new_w = int(height * aspect)
            if new_w > width:
                new_w = width
                new_h = int(width / aspect)
    elif width:
        # Resize based on width
        aspect = w / h
        new_w = width
        new_h = int(width / aspect)
    else:
        # Resize based on height
        aspect = w / h
        new_h = height
        new_w = int(height * aspect)

    # Resize the image
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return resized

def compress_image(image_bytes, quality=85, format='JPEG'):
    """
    Compress an image using PIL.

    Args:
        image_bytes: Image as bytes
        quality: JPEG compression quality (1-100)
        format: Output format (JPEG, PNG, etc.)

    Returns:
        Compressed image as bytes
    """
    image = Image.open(io.BytesIO(image_bytes))
    output = io.BytesIO()

    # Convert RGBA to RGB if saving as JPEG
    if format == 'JPEG' and image.mode == 'RGBA':
        image = image.convert('RGB')

    image.save(output, format=format, quality=quality, optimize=True)
    output.seek(0)
    return output.getvalue()

def process_s3_event(event):
    """Process an image uploaded to S3."""
    # Get the S3 bucket and key from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])

    try:
        # Download the image from S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
        image_bytes = response['Body'].read()

        # Convert bytes to OpenCV image
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

        # Process the image
        processed_image = resize_image(image, width=800)  # Resize to 800px width

        # Encode the processed image
        _, buffer = cv2.imencode('.jpg', processed_image)
        processed_bytes = buffer.tobytes()

        # Compress the image
        compressed_bytes = compress_image(processed_bytes, quality=85)

        # Generate a new key for the processed image
        filename, ext = os.path.splitext(os.path.basename(key))
        processed_key = f"processed/{filename}{ext}"

        # Upload the processed image to the processed bucket
        s3_client.put_object(
            Bucket=PROCESSED_BUCKET,
            Key=processed_key,
            Body=compressed_bytes,
            ContentType=f'image/jpeg'
        )

        # Generate a pre-signed URL for the processed image
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': PROCESSED_BUCKET, 'Key': processed_key},
            ExpiresIn=3600  # URL expires in 1 hour
        )

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps({
                'message': 'Image processed successfully',
                'original_key': key,
                'processed_key': processed_key,
                'url': url
            })
        }

    except Exception as e:
        print(f"Error processing image: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps({
                'message': f'Error processing image: {str(e)}'
            })
        }

def process_api_request(event):
    """Process an image from an API Gateway request."""
    try:
        # Parse the request body
        body = json.loads(event['body'])

        # Check if the request contains an image
        if 'image' not in body:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': 'No image provided'
                })
            }

        # Get the image data
        image_data = body['image']

        # Check if the image is a base64 string
        if image_data.startswith('data:image'):
            # Extract the base64 data
            image_data = image_data.split(',')[1]

        # Decode the base64 image
        image_bytes = base64.b64decode(image_data)

        # Get processing parameters
        width = body.get('width')
        height = body.get('height')
        quality = body.get('quality', 85)

        # Convert bytes to OpenCV image
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

        # Process the image
        processed_image = resize_image(image, width=width, height=height)

        # Encode the processed image
        _, buffer = cv2.imencode('.jpg', processed_image)
        processed_bytes = buffer.tobytes()

        # Compress the image
        compressed_bytes = compress_image(processed_bytes, quality=quality)

        # Generate a unique key for the processed image
        unique_id = str(uuid.uuid4())
        original_key = f"uploads/{unique_id}.jpg"
        processed_key = f"processed/{unique_id}.jpg"

        # Upload the original image to S3
        s3_client.put_object(
            Bucket=ORIGINAL_BUCKET,
            Key=original_key,
            Body=image_bytes,
            ContentType='image/jpeg'
        )

        # Upload the processed image to S3
        s3_client.put_object(
            Bucket=PROCESSED_BUCKET,
            Key=processed_key,
            Body=compressed_bytes,
            ContentType='image/jpeg'
        )

        # Generate pre-signed URLs
        original_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': ORIGINAL_BUCKET, 'Key': original_key},
            ExpiresIn=3600
        )

        processed_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': PROCESSED_BUCKET, 'Key': processed_key},
            ExpiresIn=3600
        )

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Image processed successfully',
                'original_key': original_key,
                'processed_key': processed_key,
                'original_url': original_url,
                'processed_url': processed_url,
                'original_size': len(image_bytes),
                'processed_size': len(compressed_bytes),
                'compression_ratio': round(len(image_bytes) / len(compressed_bytes), 2)
            })
        }

    except Exception as e:
        print(f"Error processing image: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': f'Error processing image: {str(e)}'
            })
        }

def lambda_handler(event, context):
    """
    Lambda function handler.
    Processes images from S3 events or API Gateway requests.
    """
    print("Received event:", json.dumps(event))

    # Handle OPTIONS request for CORS
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'OPTIONS,POST',
                'Access-Control-Allow-Credentials': 'true'
            },
            'body': ''
        }

    # Determine the event source
    if 'Records' in event and event['Records'][0].get('eventSource') == 'aws:s3':
        # Process S3 event
        return process_s3_event(event)
    elif 'body' in event:
        # Process API Gateway request
        return process_api_request(event)
    else:
        # Unknown event type
        print("Unknown event type:", json.dumps(event))
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps({
                'message': 'Unknown event type or malformed request'
            })
        }
