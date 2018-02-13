from urllib.request import Request, urlopen
from urllib.parse import urlparse
import json
import boto3
import string
from time import asctime
import os
from base64 import b64decode

QNAMAKER_API_KEY = os.environ['qnamaker_api_key']
lambda_client = boto3.client('lambda')
lex_client = boto3.client('lex-models')


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


def remove_invalid_punctuation(s: str) -> str:
    """Removes punctuation invalid by Lex intent rules, specifically any
    punctuation except apostrophes, underscores, and hyphens.

    Args:
        s: any string, usually name of intent.

    Returns:
        The input string without invalid punctuation.
    """
    # Create string of invalid punctuation
    invalid_punctuation = ''.join(
        [ch for ch in string.punctuation if ch not in '-_\''])
    # Remove punctuation from string
    s = s.translate(s.maketrans('', '', invalid_punctuation))
    s = s.strip()
    return s


def convert_to_intent_name(s: str) -> str:
    whitelist = set(string.ascii_lowercase + string.ascii_uppercase)
    return ''.join(filter(whitelist.__contains__, s))


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


def create_knowledge_base(faq_url: str) -> str:
    """Creates knowledge base from FAQ URL using Azure QnAMaker at
    https://qnamaker.ai/.

    Args:
        faq_url: A well-formed URL of a page containing an FAQ section.

    Returns:
        The response from the create knowledge base request.
    """
    create_request_endpoint = 'https://westus.api.cognitive.microsoft.com/qnamaker/v2.0/knowledgebases/create'
    create_request = Request(create_request_endpoint)
    create_request.add_header('Ocp-Apim-Subscription-Key', QNAMAKER_API_KEY)
    create_request.add_header('Content-Type', 'application/json')
    # TODO: call crawler to get all faq urls if the user wants it to
    input_data = str.encode(str({
        # include the time of creation in the bot title for logging
        'name': 'CAKB_' + convert_to_title(asctime()),
        'urls': [
            faq_url
        ]
    }))
    create_response = urlopen(
        create_request, data=input_data, timeout=15).read().decode('utf-8')
    return create_response


def download_knowledge_base(kbId: str) -> str:
    """Downloads knowledge base from Azure QnAMaker at https://qnamaker.ai/.

    Args:
        kbId: The id of a knowledge base in Azure QnAMaker.

    Returns:
        The knowledge base as a tab-separated string.
    """
    download_kb_request_endpoint = 'https://westus.api.cognitive.microsoft.com/qnamaker/v2.0/knowledgebases/' + kbId
    download_kb_request = Request(download_kb_request_endpoint)
    download_kb_request.add_header(
        'Ocp-Apim-Subscription-Key', QNAMAKER_API_KEY)
    download_kb_response = urlopen(download_kb_request, timeout=15).read().decode(
        'utf-8')  # returns an address from which to download kb
    # [1:-1] removes quotation marks from url
    download_kb_link = download_kb_response[1:-1]
    kb_response = urlopen(download_kb_link).read().decode(
        'utf-8-sig')  # must be utf-8-sig to remove BOM characters
    return kb_response


def generate_intents_from_knowledge_base(kb_tab_separated: str) -> list:
    """Generates a list of intent objects from knowledge base as a tab-separated
    string.

    Args:
        kb_tab_separated: A knowledge base as a tab-separated string.

    Returns:
        A list of intent objects that each contain an intent name, a list of
        sample utterances, and a response.
    """
    lines = kb_tab_separated.split('\r')
    # the first line are just headers; the last line is empty
    lines = lines[1:-1]
    lines = [line.split('\t') for line in lines]

    intents = [{
        # only take first 65 characters, full intent name <100 characters
        'name': convert_to_intent_name(question)[:65],
        'sample_utterances': [remove_invalid_punctuation(question)],
        'response': answer
    } for question, answer, source in lines]

    return intents


def invoke_function(func_name: str, invoc_type: str, payload: object) -> str:
    """Invokes the Lambda function specified by the arguments.

    Args:
        func_name: name of the Lambda function to be called.
        invoc_type: type of invocation as defined in boto3 documentation.
        payload: an object to pass to the Lambda function.

    Returns:
        The response from the Lambda function.
    """
    response = ''
    try:
        response = lambda_client.invoke(
            FunctionName=func_name,
            InvocationType=invoc_type,
            Payload=json.dumps(payload)
        )
    except Exception as e:
        raise e
    return response


def delete_knowledge_base(kbId: str) -> None:
    """Deletes knowledge base from Azure QnAMaker at https://qnamaker.ai/.

    Args:
        kbId: The id of a knowledge base in Azure QnAMaker.
    """
    delete_request_endpoint = 'https://westus.api.cognitive.microsoft.com/qnamaker/v2.0/knowledgebases/' + kbId
    delete_request = Request(delete_request_endpoint, method='DELETE')
    delete_request.add_header('Ocp-Apim-Subscription-Key', QNAMAKER_API_KEY)
    delete_response = urlopen(
        delete_request, timeout=15).read().decode('utf-8')


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


def lambda_handler(event, context):
    # TODO: Check urlopen responses for success and deal with endpoint
    faq_url = event['url']
    bot_name = bot_name_from_url(faq_url)

    # Return package
    response_info = {
        'already_made': True,
        'creating': False,
        'bot_name': bot_name,
        'error_message': ''
    }

    # Check if bot is already there
    try:
        lex_client.get_bot(name=bot_name, versionOrAlias='DEV')
        print('Returned bot name')
        return get_response_package(response_info)
    except Exception as e:
        print(bot_name, 'not found')
        print('Starting pipeline...')

    # TODO: Async calls to Azure

    # Create knowledge base from faq url
    create_response = create_knowledge_base(faq_url)
    create_response_json = json.loads(create_response)
    kbId = create_response_json['kbId']  # kb = knowledge base

    # Download the generated knowledge base
    kb_response = download_knowledge_base(kbId)
    intents = generate_intents_from_knowledge_base(kb_response)

    # Assemble payload for other Lambda functions
    payload = {
        'bot_name': bot_name,
        'intents': intents
    }

    # Invoke CreateLexBot
    create_lex_response_table_response = invoke_function(
        'CreateLexResponseTable', 'Event', payload)
    create_lex_bot_response = invoke_function('CreateLexBot', 'Event', payload)

    # Delete knowledge base after done with it
    delete_knowledge_base(kbId)

    response_info['already_made'] = False
    response_info['creating'] = True
    return get_response_package(response_info)
