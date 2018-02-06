import boto3
import time

lex_client = boto3.client('lex-models')
ddb_client = boto3.client('dynamodb')

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
                nameContains=intent_prefix
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
    try:
        lex_client.delete_bot_alias(
            name='DEV',
            botName=bot_name
        )
    except Exception as e:
        print(e)
    try:
        lex_client.delete_bot(
            name=bot_name
        )
    except Exception as e:
        print(e)

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
            except NotFoundException:
                break
            except Exception as e:
                print(e)
            time.sleep(2)

def delete_table(table_name):
	"""Deletes table of intents and responses.

	Args:
		table_name: name of the table to delete.
	"""
    ddb_client.delete_table(TableName=table_name)

def lambda_handler(event, context):
    bot_name = event['bot_name']
    table_name = bot_name + '_intents'
    intents_to_delete = get_intents_to_delete(bot_name)

    delete_bot(bot_name)
    delete_intents(intents_to_delete)
    delete_table(table_name)

    return True
