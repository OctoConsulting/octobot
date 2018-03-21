import boto3
import lexinterface as lx
from main import bot_name_from_url
import status
import sys
import time

ddb_client = boto3.client('dynamodb', region_name='us-east-1')
lex_client = boto3.client('lex-models', region_name='us-east-1')


def get_intents_to_delete(bot_name: str) -> list:
    """Finds the intent names to delete from the DynamoDB tracker.

    Args:
        bot_name: The name of the bot.

    Returns:
        A list of intent names to be deleted.
    """
    table_name = bot_name + '_intents'
    try:
        scan_response = ddb_client.scan(
            TableName=table_name,
            ProjectionExpression='intent'
        )
    except Exception as e:
        return []
    intents = []
    if 'Items' in scan_response:
        for obj in scan_response['Items']:
            intents.append(obj['intent']['S'])
    return intents

def delete_intent_table(table_name: str) -> None:
    """Delete table of intents for bot.

    Args:
        table_name: The name of the table.
    """
    try:
        ddb_client.delete_table(TableName=table_name)
    except Exception as e:
        pass

def wipe_bot(args: str) -> None:
    """Remove bot from all of AWS.

    Args:
        args: Dictionary mapping url.
    """
    faq_url = args['url']
    bot_name = bot_name_from_url(faq_url)

    status.update_bot_stage(bot_name, 'DELETING')

    lx.delete_bot(bot_name)
    intents_to_delete = get_intents_to_delete(bot_name)
    if len(intents_to_delete) > 0:
        lx.delete_intents(intents_to_delete)

    table_name = bot_name + '_intents'
    delete_intent_table(table_name)

    status.delete_bot(bot_name)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        rcode = wipe_bot({'url': sys.argv[1]})
        # print(response_codes[rcode])
    else:
        print('Call must be of form "python3 delete.py <url>"')

