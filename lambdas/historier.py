import json
import boto3
from decimal import Decimal

# Initialize DynamoDB
dynamodb_resource = boto3.resource('dynamodb')
table = dynamodb_resource.Table('ImageMetadata')

# Reusing DecimalEncoder to avoid "Object of type Decimal is not JSON serializable"
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    try:
        # Retrieve the 10 most recent entries
        # Note: Scan doesn't guarantee order, but it gets the data flowing
        response = table.scan(Limit=10)
        items = response.get('Items', [])
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*', 
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET,OPTIONS',
                'Content-Type': 'application/json'
            },
            'body': json.dumps(items, cls=DecimalEncoder)
        }
            
    except Exception as e:
        print(f"History Error: {e}")
        return {
            'statusCode': 500,
            'headers': { 'Access-Control-Allow-Origin': '*' },
            'body': json.dumps({'error': str(e)})
        }