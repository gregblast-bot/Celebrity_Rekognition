import json
import boto3
from decimal import Decimal

# Initialize DynamoDB
dynamodb_resource = boto3.resource('dynamodb')
table = dynamodb_resource.Table('ImageMetadata')

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    image_id = event.get('queryStringParameters', {}).get('imageID')
    
    try:
        response = table.get_item(Key={'ImageID': image_id})
        
        # Check if the item actually exists before accessing it
        if 'Item' in response:
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*', # Required for CORS
                    'Content-Type': 'application/json'
                },
                'body': json.dumps(response['Item'])
            }
        else:
            # Item not found yet, tell frontend to keep waiting
            return {
                'statusCode': 200, # Return 200 so the frontend doesn't see an "error"
                'headers': { 'Access-Control-Allow-Origin': '*' },
                'body': json.dumps({'Status': 'PROCESSING'})
            }
            
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }