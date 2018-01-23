import boto3

def lambda_handler(event, context):
    bot_name = event['bot_name']
    intents = event['intents']
    
    # TODO: add exception handling to create table if not exists
    ddb_client = boto3.client('dynamodb')
    create_table_response = ddb_client.create_table(
        TableName=(bot_name + '_intents'),
        KeySchema=[
            {
                'AttributeName': 'intent',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'version',
                'KeyType': 'RANGE'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'intent',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'version',
                'AttributeType': 'S'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )
    
    # TODO: put intent->response pairs into table
    
    print("response:", create_table_response)
    
    return 'Hello from Lambda'
