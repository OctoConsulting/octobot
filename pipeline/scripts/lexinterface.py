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


def clean_utterance(utterance: str) -> str:
    """Clean utterance to make it fit the right length and character set.

    Args:
        utterance: The utterance string.

    Returns:
        The utterance that meets Lex specifications.
    """
    stopwords = ['i', 'to', 'a', 'an', 'the']
    new_utterance = ' '.join([w for w in utterance.split() if w.lower() not in stopwords])
    new_utterance = new_utterance[:100]
    return new_utterance

def clean_intent_name(intent: str) -> str:
    """Clean intent to make it fit the right length and character set.

    Args:
        intent: The intent name string.

    Returns:
        The intent that meets Lex specifications.
    """ 
    new_intent = intent[:86]  # max 100 characters but must account for prepended
                                   # lex-us-east-1-
    return new_intent

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
        # unneeded: clean_intent_name(cur_intent_name)
        #           cur_sample_utterances = [clean_utterance(i) for i in intent['sample_utterances']]
        cur_sample_utterances = intent['sample_utterances']
        try:
            lex_client.put_intent(
                name=cur_intent_name,
                sampleUtterances=cur_sample_utterances,
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
    for n in range(10):  # Max number of attempts
        try:
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
            break
        except Exception as e:
            time.sleep(10)
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

qnamaker_api_key: 'ca294f56e7124392bc34eeffdd2f8d67'
def delete_bot(bot_name: str) -> None:
    """Deletes the defined bot alias and the bot itself.
    
    Args:
        bot_name: name of the bot to delete.
    """
    for n in range(10):  # Max of 10 tries
        try:
            lex_client.delete_bot_alias(
                name='DEV',
                botName=bot_name
            )
        except Exception as e:
            try:
                exception_name = e.response['Error']['Code']
            except:
                break
            if exception_name == 'NotFoundException':
                break
            else:
                print(e)
                time.sleep(2)
        else:
            break
    else:
        print('Deleting bot alias failed.')
        return

    for n in range(10):  # Max of 10 tries
        try:
            lex_client.delete_bot(
                name=bot_name
            )
        except Exception as e:
            try:
                exception_name = e.response['Error']['Code']
            except:
                break
            if exception_name == 'NotFoundException':
                break
            else:
                print(e)
            time.sleep(2)
        else:
            break
    else:
        print('Deleting bot failed.')
        return

def delete_intents(intent_names: list) -> None:
    """Deletes all intents provided, normally associated with a bot.

    Args:
        intent_names: list of intent names, normally associated with a bot.
    """
    for intent_name in intent_names:
        for n in range(10):  # Max of 10 tries
            try:
                lex_client.delete_intent(name=intent_name)
                break
            except Exception as e:
                exception_name = e.response['Error']['Code']
                if exception_name == 'NotFoundException':
                    break
                else:
                    print(e)
                    time.sleep(2)
            time.sleep(2)

