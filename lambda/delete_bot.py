import boto3
import string
import time
from botocore.exceptions import ClientError
from urllib.parse import urlparse

lex_client = boto3.client('lex-models')
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


def get_intents_to_delete(bot_name: str) -> list:
    """Generates a list of intents associated with the bot.

    Args:
        bot_name: name of the bot to delete.

    Returns:
        The list of intents associated with the bot.
    """
    intent_prefix = bot_name + '_'
    intents_to_delete = []
    nextToken = ''
    for n in range(1000):  # Already a max of 1000 intents per account
        if not nextToken:
            response = lex_client.get_intents(
                maxResults=50,
                nameContains=intent_prefix,
                nextToken=''
            )
        else:
            response = lex_client.get_intents(
                maxResults=50,
                nameContains=intent_prefix,
                nextToken=nextToken
            )
        for intent in response['intents']:
            intents_to_delete.append(intent['name'])
        if 'nextToken' not in response:
            break
        nextToken = response['nextToken']
    return intents_to_delete


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
        except ClientError as e:
            exception_name = e.response['Error']['Code']
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
        except ClientError as e:
            exception_name = e.response['Error']['Code']
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
            except ClientError as e:
                exception_name = e.response['Error']['Code']
                if exception_name == 'NotFoundException':
                    break
                else:
                    print(e)
                    time.sleep(2)
            time.sleep(2)


def delete_table(table_name):
    """Deletes table of intents and responses.

    Args:
        table_name: name of the table to delete.
    """
    try:
        ddb_client.delete_table(TableName=table_name)
    except ClientError as e:
        exception_name = e.response['Error']['Code']
        print(e)


def get_response_package(response_info: object) -> object:
    """Generates a response package in line with API Gateway requirements.

    Args:
        response_info: a json object containing any custom information.

    Returns:
        A package in the format specified by API Gateway return requirements.
    """
    return {
        'isBase64Encoded': 'false',
        'statusCode': 200,
        'headers': {},
        'body': json.dumps(response_info)
    }


def declare_bot_not_exists(bot_name):
    """Delete bot from octochat_bots table to signify it no longer exists.

    Args:
        bot_name: name of bot.
    """
    try:
        ddb_client.delete_item(
            TableName='octochat_bots',
            Key={
                'name': {
                    'S': bot_name
                }
            }
        )
    except Exception as e:
        print(e)


def lambda_handler(event, context):
    faq_url = event['url']
    bot_name = bot_name_from_url(faq_url)

    table_name = bot_name + '_intents'
    intents_to_delete = get_intents_to_delete(bot_name)

    delete_bot(bot_name)
    delete_intents(intents_to_delete)
    delete_table(table_name)
    declare_bot_not_exists(bot_name)

    response_info = {
        'bot_name': bot_name
    }
    return get_response_package(response_info)
