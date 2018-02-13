import boto3
import time

lex_client = boto3.client('lex-models')


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


def create_intent_versions(intents):
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


def lambda_handler(event, context):
    assert 'intents' in event and len(event['intents']) > 0

    intents = event['intents']
    bot_name = event['bot_name']

    create_intents(bot_name, intents)

    intents_name_version_list = [{
        'intentName': bot_name + '_' + intent['name'],
        'intentVersion': '1'
    } for intent in intents]

    create_intent_versions(intents_name_version_list)

    create_bot_response = create_bot(bot_name, intents_name_version_list)

    lex_client.create_bot_version(name=bot_name)

    for n in range(80):
        try:
            lex_client.put_bot_alias(
                name='DEV',
                botVersion='1',
                botName=bot_name
            )
            break
        except:
            print('error', n)
        time.sleep(3)

    return str(create_bot_response)
