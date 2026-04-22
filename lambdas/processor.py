import boto3
import json
import uuid
import urllib.parse

rekognition = boto3.client('rekognition', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb').Table('ImageMetadata')
bedrock = boto3.client('bedrock-runtime')

def get_fun_fact(name):
    """Calls Amazon Bedrock to get a fun fact about the celebrity."""
    prompt = f"Provide one short, surprising fun fact about {name} in 25 words or less."
    
    # Using Claude 3 (Haiku is fast and cheap for this).
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 100,
        "messages": [{"role": "user", "content": prompt}]
    })
    
    try:
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            body=body
        )
        response_body = json.loads(response.get('body').read())
        return response_body['content'][0]['text']
    except Exception as e:
        return "Could not fetch fun fact at this time."

def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    # Decode the key to handle spaces and special characters.
    raw_key = event['Records'][0]['s3']['object']['key']
    key = urllib.parse.unquote_plus(raw_key)

    print(f"Analyzing bucket: {bucket} with key: {key}")
    
    # Rekognition setup.
    res = rekognition.recognize_celebrities(Image={'S3Object':{'Bucket':bucket,'Name':key}})
    
    results = []
    for celeb in res.get('CelebrityFaces', []):
        name = celeb['Name']
        # Bedrock Fun Fact.
        fun_fact = get_fun_fact(name)
        
        results.append({
            "Name": name,
            "FunFact": fun_fact,
            "IMDB": next((u for u in celeb.get('Urls', []) if "imdb" in u), "N/A"),
            "Social": f"https://x.com/search?q={urllib.parse.quote_plus(name)}"
        })

    # Store in DynamoDB (using the file name as the ID so the frontend can find it).
    final_status = 'COMPLETED' if results else 'NO_CELEBRITIES_FOUND'
    
    dynamodb.put_item(Item={
        'ImageID': key, 
        'CelebrityData': results,
        'Status': final_status
    })

    return {"status": "success"}