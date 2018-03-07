import boto3
import time

ddb_client = boto3.client('dynamodb', region_name='us-east-1')
lex_client = boto3.client('lex-models', region_name='us-east-1')

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


def iterate_batch_write_item(table_name: str, put_requests: list) -> None:
    """Batch write items to table while handling more than 25 items.

    Args:
        table_name: name of table to put items to.
        put_requests: list of put requests.
    """
    num_put_requests = len(put_requests)
    for n in range(0, num_put_requests, 25):
        ddb_client.batch_write_item(
            RequestItems={
                table_name: put_requests[n:n + 25]
            }
        )


def create_intents(bot_name: str, intents: list) -> None:
    """Create Lex intents from intent objects list. All intents have the same
    fulfillment activity code hook to the Lambda function LexResponder.

    Args:
        bot_name: name of bot to be created.
        intents: a list of intent objects where each intent object defines the
            intent name, a list sample utterances, and a response.
    """
    for intent in intents:
        # TODO: add exception handling to handle if intent already exists
        cur_intent_name = bot_name + '_' + intent['name']
        try:
            lex_client.put_intent(
                name=cur_intent_name,
                sampleUtterances=intent['sample_utterances'],
                fulfillmentActivity={
                    'type': 'CodeHook',
                    'codeHook': {
                        'uri': 'arn:aws:lambda:us-east-1:749091557667:function:LexResponder',
                        'messageVersion': '1.0'
                    }
                },
            )
        except Exception as e:
            print(e)


def create_intent_versions(intents: list) -> None:
    """Publish a version for each intent.

    Args:
        intents: The list of intents with intentName defined for each intent.
    """
    for intent in intents:
        try:
            lex_client.create_intent_version(
                name=intent['intentName']
            )
        except Exception as e:
            print(e)


def create_bot(bot_name: str, intents_name_version_list: list) -> str:
    """Create Lex bot with all specified intents attached.

    Args:
        bot_name: name of bot to be created.
        intents_name_version_list: a list of intent objects where each intent
            object defines the intent name and version.
    """
    # TODO: add exception handling to handle if bot already exists
    create_bot_response = lex_client.put_bot(
        name=bot_name,
        intents=intents_name_version_list,
        clarificationPrompt={
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': 'Sorry, can you repeat that?'
                }
            ],
            'maxAttempts': 3,
            'responseCard': 'Response card for clarificationPrompt'
        },
        abortStatement={
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': 'Sorry, I don\'t think I know how to help you.'
                }
            ],
            'responseCard': 'Response card for abortStatement'
        },
        idleSessionTTLInSeconds=123,
        voiceId='Kendra',
        locale='en-US',
        childDirected=False
    )
    return create_bot_response


def create_bot_version(bot_name: str) -> None:
    """Publish version of bot.

    Args:
        bot_name: The name of the bot.
    """
    lex_client.create_bot_version(name=bot_name)

def create_bot_alias(bot_name: str, max_attempts: int = 80) -> None:
    """Assign the DEV alias to the bot.

    Args:
        bot_name: The name of the bot.
        max_attempts: The number of attempts to assign alias before giving up.
    """
    for n in range(max_attempts):
        try:
            lex_client.put_bot_alias(
                name='DEV',
                botVersion='1',
                botName=bot_name
            )
            return True
        except:
            print('error', n)
        time.sleep(3)
    return False
