import json
import os
import boto3
import base64
import uuid
from datetime import datetime

# Get environment variables for S3 buckets
ORIGINAL_BUCKET = os.environ.get('ORIGINAL_BUCKET', 'serverless-image-processor-original-1746555636-3279')
PROCESSED_BUCKET = os.environ.get('PROCESSED_BUCKET', 'serverless-image-processor-processed-1746555636-3279')

# Initialize S3 client
s3_client = boto3.client('s3')

def lambda_handler(event, context):
    """
    Lambda function handler for image processing.
    """
    print("Received event:", json.dumps(event))
    print(f"Using buckets: Original={ORIGINAL_BUCKET}, Processed={PROCESSED_BUCKET}")

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

    # Process API request
    try:
        # Log the entire event for debugging
        print("Full event:", json.dumps(event))

        # Check if body exists
        if 'body' not in event:
            print("Error: 'body' not in event")
            return error_response("No body in event")

        # Check if body is empty
        if not event['body']:
            print("Error: event['body'] is empty")
            return error_response("Empty body in event")

        # Log the body
        print("Body type:", type(event['body']))
        print("Body content:", event['body'][:100] + "..." if len(event['body']) > 100 else event['body'])

        # Parse the request body
        try:
            body = json.loads(event['body'])
            print("Parsed body:", json.dumps(body)[:100] + "..." if len(json.dumps(body)) > 100 else json.dumps(body))
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {str(e)}")
            return error_response(f"Invalid JSON in request body: {str(e)}")

        # Check if the request contains an image
        if 'image' in body:
            # Get the image data
            image_data = body['image']

            # Check if the image is a base64 string
            if image_data.startswith('data:image'):
                # Extract the base64 data
                content_type = image_data.split(';')[0].split(':')[1]
                base64_data = image_data.split(',')[1]
                image_bytes = base64.b64decode(base64_data)

                # Generate unique IDs for the files
                unique_id = str(uuid.uuid4())
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                file_id = f"{timestamp}_{unique_id}"

                # Define file paths
                original_key = f"uploads/{file_id}.jpg"
                processed_key = f"processed/{file_id}.jpg"

                # Upload original image to S3
                print(f"Uploading original image to {ORIGINAL_BUCKET}/{original_key}")
                s3_client.put_object(
                    Bucket=ORIGINAL_BUCKET,
                    Key=original_key,
                    Body=image_bytes,
                    ContentType=content_type
                )

                # For now, we'll just copy the original image to the processed bucket
                # In a production environment, you would use a properly configured Lambda layer for image processing
                print("Copying original image to processed bucket...")

                # Get requested parameters (for information only, not used in processing yet)
                width = body.get('width', 800)  # Default to 800px width
                height = body.get('height', None)  # Default to None (maintain aspect ratio)
                quality = body.get('quality', 85)  # Default to 85% quality

                print(f"Requested parameters: width={width}, height={height}, quality={quality}")
                print(f"Note: Image processing is disabled in this version. Using original image.")

                # Upload the original image to the processed bucket
                print(f"Uploading to {PROCESSED_BUCKET}/{processed_key}")
                s3_client.put_object(
                    Bucket=PROCESSED_BUCKET,
                    Key=processed_key,
                    Body=image_bytes,
                    ContentType=content_type
                )

                # Use the original image bytes for now
                processed_bytes = image_bytes

                # Generate pre-signed URLs for the images
                original_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': ORIGINAL_BUCKET, 'Key': original_key},
                    ExpiresIn=3600  # URL expires in 1 hour
                )

                processed_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': PROCESSED_BUCKET, 'Key': processed_key},
                    ExpiresIn=3600  # URL expires in 1 hour
                )

                # Calculate compression ratio
                compression_ratio = len(image_bytes) / len(processed_bytes) if len(processed_bytes) > 0 else 1.0

                # Return success response
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
                        'original_key': original_key,
                        'processed_key': processed_key,
                        'original_url': original_url,
                        'processed_url': processed_url,
                        'original_size': len(image_bytes),
                        'processed_size': len(processed_bytes),
                        'compression_ratio': round(compression_ratio, 2),
                        'width': width,
                        'height': height,
                        'quality': quality
                    })
                }
            else:
                return error_response("Invalid image format. Expected base64 data URI.")
        else:
            return error_response("No image provided in the request.")

    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return error_response(f"Error processing request: {str(e)}")

def error_response(message):
    """Generate an error response with CORS headers."""
    return {
        'statusCode': 400,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'OPTIONS,POST'
        },
        'body': json.dumps({
            'message': message
        })
    }
