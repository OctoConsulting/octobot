import boto3
import json
import string
from urllib.parse import urlparse

ddb_client = boto3.client('dynamodb')

def bot_name_from_url(url: str) -> str:
    """Makes a unique bot name from the base url from the base url and the
    path url.

    Args:
        url: A well-formed URL.

    Returns:
        The base url as a titlecased, no-space, no-puncutation string.
    """
    base_url = urlparse(url).netloc
    path = urlparse(url).path
    path_parts = path.split('/')[1:]  # [1:] because first is always empty
    path_hash = ''.join([pp[:2] for pp in path_parts])[
        :10]  # "hash" the rest of the url
    return convert_to_title(base_url + path_hash)


def convert_to_title(s: str) -> str:
    """Formats string as a title, such that the input string has no punctuation,
    is titlecased, and has no whitespace.

    Args:
        s: any string.

    Returns:
        The input string as a title.
    """
    # Remove punctuation
    s = s.translate(s.maketrans('', '', string.punctuation))
    s = s.title()
    # Remove whitespace
    s = s.translate(s.maketrans('', '', string.whitespace))
    return s


def lambda_handler(event, context):
    print(event)
    response_payload = {
        'isBase64Encoded': 'false',
        'statusCode': 200,
        'headers': {
'           Access-Control-Allow-Origin': '*'
        },
        'body': '{}'
    }

    if 'queryStringParameters' not in event:
        response_payload['statusCode'] = '401'
        return response_payload
    if 'url' not in event['queryStringParameters']:
        response_payload['statusCode'] = '401'
        return response_payload
        
    url = event['queryStringParameters']['url']
    bot_name = bot_name_from_url(url)
        
    try:
        response_item = ddb_client.get_item(
            TableName='octochat_bots',
            Key={
                'name': {
                    'S': bot_name
                }
            },
            AttributesToGet=[
                'stage'
            ]
        )
        if 'Item' in response_item:
            response_payload['body'] = json.dumps({
                'bot_name': bot_name,
                'status': response_item['Item']['stage']['S']
            })
        else:
            response_payload['statusCode'] = 400
    except:
        response_payload['statusCode'] = 400
        
    return response_payload

