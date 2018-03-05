import boto3
import string
import sys
from urllib.parse import urlparse

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


def main(event):
    faq_url = event['url']
    print(faq_url)
    print(bot_name_from_url(faq_url))


if __name__ == '__main__':
    if len(sys.argv) == 2:
        main({'url': sys.argv[1]})
