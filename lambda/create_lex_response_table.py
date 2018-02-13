import boto3
import time

ddb_client = boto3.client('dynamodb')


def create_dynamodb_table(table_name: str) -> str:
    """Create a DynamoDB table for intents, with primary keys of intent and the
    version.

    Args:
        table_name: name of the table unique to the FAQ.

    Returns:
        The response generated from the create table request.
    """
    # TODO: add exception handling to create table if not exists
    create_table_response = ddb_client.create_table(
        TableName=table_name,
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
    return create_table_response


def wait_until_table_ready(table_name: str, max_iterations: int=10) -> bool:
    """Indicates when the DynamoDB table is ready.

    Args:
        table_name: name of the table in DynamoDB.
        max_iterations: max number of tries, separated by 3 seconds, before
            giving up and returning False.

    Returns:
        Returns True if table is ready. Returns False if the table is not ready 
            after `max_iterations` number of checks, separated by 3 seconds.
    """
    iteration_count = 0
    while iteration_count < max_iterations:
        # TODO: add error handling
        describe_table_response = ddb_client.describe_table(
            TableName=table_name
        )
        table_status = describe_table_response['Table']['TableStatus']
        if table_status == 'ACTIVE':
            return True
        iteration_count += 1
        time.sleep(3)
    return False


def put_request(bot_name: str, intent: object) -> object:
    """Wrap the bot name and intent information in a put request object.

    Args:
        bot_name: name of the bot.
        intent: intent object that includes at least the name and response.

    Returns:
        The put request object.
    """
    return {
        'PutRequest': {
            'Item': {
                'intent': {
                    'S': bot_name + '_' + intent['name']
                },
                'version': {
                    'S': '$LATEST'
                },
                'response': {
                    'S': intent['response']
                }
            }
        }
    }


def lambda_handler(event, context):
    bot_name = event['bot_name']
    intents = event['intents']

    table_name = bot_name + '_intents'
    create_dynamodb_table(table_name)

    if not wait_until_table_ready(table_name, 10):
        return 'Table not ready in time, try again.'

    # TODO: make version reflect the correct version
    put_requests = [put_request(bot_name, intent) for intent in intents]
    batch_write_item_response = ddb_client.batch_write_item(
        RequestItems={
            table_name: put_requests
        }
    )

    return str(batch_write_item_response)
