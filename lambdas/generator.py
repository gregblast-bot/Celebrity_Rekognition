import boto3
import json
from botocore.config import Config

def lambda_handler(event, context):
    params = event.get('queryStringParameters') or {}
    file_name = params.get('fileName', 'image.jpg')
    content_type = params.get('contentType', 'image/jpeg')
    
    BUCKET_NAME = 'project-locker-wagonblast-2026'

    # Configure S3.
    s3_config = Config(
        region_name='us-east-1',
        signature_version='s3v4',
        s3={'addressing_style': 'virtual'}
    )
    s3 = boto3.client('s3', config=s3_config)

    try:
        # Now that file_name is defined, generate the URL.
        url = s3.generate_presigned_url(
            ClientMethod='put_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': file_name,
                'ContentType': content_type
            },
            ExpiresIn=300
        )
        
        return {
            'statusCode': 200,
            'headers': {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "OPTIONS,GET,PUT"
            },
            'body': json.dumps({
                'uploadURL': url, 
                'fileName': file_name
            })
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': { "Access-Control-Allow-Origin": "*" },
            'body': json.dumps({'error': str(e)})
        }