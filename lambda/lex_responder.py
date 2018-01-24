import boto3

def lambda_handler(event, context):
    bot_name = event['bot']['name']
    current_intent_name = event['currentIntent']['name']
    
    table_name = bot_name + '_intents'
    ddb_client = boto3.client('dynamodb')
    
    # TODO: add error handling
    get_item_response = ddb_client.get_item(
        TableName=table_name,
        Key={
            'intent': {
                'S': current_intent_name
            },
            'version': {
                'S': '$LATEST'
            }
        }
    )
    response_text = str(get_item_response['Item']['response']['S'])
    
    return_package = {
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': 'Fulfilled',
            'message': {
                'contentType': 'PlainText',
                'content': response_text
            }
        }
    }
    
    return return_package