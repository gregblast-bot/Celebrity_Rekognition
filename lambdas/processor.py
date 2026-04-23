import boto3
import json
import uuid
import urllib.parse

rekognition = boto3.client('rekognition', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb').Table('ImageMetadata')
bedrock = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')

def get_fun_fact(name):
    # Standard 2026 Claude Messages Payload
    prompt_config = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 300,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": f"One unique fun fact about {name}. Under 20 words."}]
            }
        ]
    }
    
    try:
        # April 2026 Global Inference ID
        model_id = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
        
        response = bedrock.invoke_model(
            body=json.dumps(prompt_config),
            modelId=model_id, 
            accept="application/json",
            contentType="application/json"
        )
        
        response_body = json.loads(response.get('body').read())
        return response_body['content'][0]['text'].strip()
        
    except Exception as e:
        # This will now show in CloudWatch because of the 60s timeout
        print(f"Bedrock Error: {str(e)}") 
        return "Fact temporarily unavailable."

def lambda_handler(event, context):
    # Parse S3 event.
    bucket = event['Records'][0]['s3']['bucket']['name']
    raw_key = event['Records'][0]['s3']['object']['key']
    key = urllib.parse.unquote_plus(raw_key)

    print(f"Analyzing bucket: {bucket} with key: {key}")
    
    try:
        # Call Rekognition.
        res = rekognition.recognize_celebrities(Image={'S3Object':{'Bucket':bucket,'Name':key}})
        
        results = []
        # .Loop through recognized faces.
        for celeb in res.get('CelebrityFaces', []):
            name = celeb.get('Name', 'Unknown')
            
            # Get the IMDB link from Rekognition metadata.
            rekog_urls = celeb.get('Urls', [])
            imdb_link = next((url for url in rekog_urls if "imdb.com" in url), "N/A")
            
            # Get Bedrock Fun Fact.
            fun_fact = get_fun_fact(name)
            
            # Build the clean object for the UI.
            results.append({
                "Name": name,
                "FunFact": fun_fact,
                "IMDB": imdb_link,
                "Social": f"https://x.com/search?q={urllib.parse.quote_plus(name)}"
            })

        # Determine final status and save to DynamoDB.
        final_status = 'COMPLETED' if results else 'NO_CELEBRITIES_FOUND'
        
        dynamodb.put_item(Item={
            'ImageID': key,
            'CelebrityData': results,
            'Status': final_status
        })

        return {"status": "success", "found": len(results)}

    except Exception as e:
        print(f"Processing Error: {str(e)}")
        # Update DynamoDB with FAILED status so frontend stops polling.
        dynamodb.put_item(Item={
            'ImageID': key,
            'Status': 'FAILED',
            'Error': str(e)
        })
        return {"status": "error", "message": str(e)}