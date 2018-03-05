import boto3
import json
import string
from time import asctime
from urllib.request import Request, urlopen
import yaml


def get_API_key() -> None:
    """Grab QnAMaker API key from encrypted s3 object.
    """
    s3_client = boto3.client('s3')
    response = s3_client.get_object(
        Bucket='octochat-processor',
        Key='secrets.yml'
    )
    data = yaml.load(response['Body'])
    return data['qnamaker_api_key']


def create_knowledge_base(faq_url: str, QNAMAKER_API_KEY: str) -> str:
    """Creates knowledge base from FAQ URL using Azure QnAMaker at
    https://qnamaker.ai/.

    Args:
        faq_url: A well-formed URL of a page containing an FAQ section.
        QNAMAKER_API_KEY: The API key for QnAMaker.

    Returns:
        The knowledge base ID.
    """
    create_request_endpoint = 'https://westus.api.cognitive.microsoft.com/qnamaker/v2.0/knowledgebases/create'
    create_request = Request(create_request_endpoint)
    create_request.add_header('Ocp-Apim-Subscription-Key', QNAMAKER_API_KEY)
    create_request.add_header('Content-Type', 'application/json')
    # TODO: call crawler to get all faq urls if the user wants it to
    input_data = str.encode(str({
        # include the time of creation in the bot title for logging
        'name': 'CAKB_' + asctime(),
        'urls': [
            faq_url
        ]
    }))
    create_response = urlopen(
        create_request, data=input_data, timeout=15).read().decode('utf-8')
    kbId = json.loads(create_response)['kbId']
    return kbId


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


def get_stopwords() -> list:
    """Retrieve list of stopwords.

    Returns:
        A list of stopwords retrieved from stopwords.txt.
    """
    with open('stopwords.txt', 'r') as f:
        return f.read().split('\n')


def question_to_intent_name(s: str, stopwords: list) -> str:
    """Converts a question string to an intent name.

    Args:
        s: The question string.
        stopwords: The list of stopwords to remove from the string.

    Returns:
        A condensed version of the question text as an intent name.
    """
    tokens = s.split(' ')
    tokens = [t for t in tokens if t.lower() not in stopwords]
    filtered_question = ''.join(tokens)
    whitelist = set(string.ascii_lowercase + string.ascii_uppercase)
    return ''.join(filter(whitelist.__contains__, filtered_question))


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
    stopwords = get_stopwords()

    intents = [{
        # only take first 65 characters, full intent name <100 characters
        'name': question_to_intent_name(question, stopwords)[:65],
        'sample_utterances': [remove_invalid_punctuation(question)],
        'response': answer
    } for question, answer, source in lines]

    return intents


def download_knowledge_base(kbId: str, QNAMAKER_API_KEY: str) -> str:
    """Downloads knowledge base from Azure QnAMaker at https://qnamaker.ai/.

    Args:
        kbId: The id of a knowledge base in Azure QnAMaker.
        QNAMAKER_API_KEY: The API key from QnAMaker.

    Returns:
        The knowledge base as a list of intents..
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
    intents = generate_intents_from_knowledge_base(kb_response)
    return intents


def delete_knowledge_base(kbId: str, QNAMAKER_API_KEY: str) -> None:
    """Deletes knowledge base from Azure QnAMaker at https://qnamaker.ai/.

    Args:
        kbId: The id of a knowledge base in Azure QnAMaker.
        QNAMAKER_API_KEY: The API key for QnAMaker.
    """
    delete_request_endpoint = 'https://westus.api.cognitive.microsoft.com/qnamaker/v2.0/knowledgebases/' + kbId
    delete_request = Request(delete_request_endpoint, method='DELETE')
    delete_request.add_header('Ocp-Apim-Subscription-Key', QNAMAKER_API_KEY)
    delete_response = urlopen(
        delete_request, timeout=15).read().decode('utf-8')
