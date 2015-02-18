import string
import tweepy

from credentials import (
    consumer_key, consumer_secret,
    access_token, access_token_secret
)
from models import Stopword
from collections import Counter


class Service(object):

    # Map uppercase to lowercase, and deletes any punctuation.
    trans = {ord(string.ascii_uppercase[i]): ord(string.ascii_lowercase[i])
             for i in range(26)}
    trans.update({ord(c): None for c in string.punctuation + string.digits})

    def __init__(self):
        self._tw_api = None

    @property
    def tw_api(self):
        """Tweepy API client."""
        if self._tw_api is None:
            auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
            auth.set_access_token(access_token, access_token_secret)
            self._tw_api = tweepy.API(auth)
        return self._tw_api

    def fetch(self, query, limit=100):
        """Fetches search results for the given query.

        TODO(kanat): Figure out why result_type='popular' results < limit.
        """
        #return list(tweepy.Cursor(
        #    self.tw_api.search,
        #    q=query,
        #    lang='en',
        #    result_type='popular').items(limit))
        return self.tw_api.search(q=query, count=limit,
                                  result_type='popular', lang='en')

    @staticmethod
    def top_hashtags(tweets, limit=5):
        """Extracts most frequent hashtags from given tweets."""
        hashtags = Counter()
        for t in tweets:
            for h in t.entities['hashtags']:
                if 'text' in h:
                    hashtags[h['text'].lower()] += 1
        top = hashtags.most_common(limit)
        return ['#' + t[0] for t in top]

    @staticmethod
    def top_keywords(tweets, limit=5):
        """Extracts most frequent keywords from given tweets.

        TODO(kanat): Use stopwords. Refer to _token_okay().
        """
        words = Counter()
        for t in tweets:
            for token in set(t.text.split()):
                words[token.lower()] += 1
        top = words.most_common(limit)
        return [t[0] for t in top]


def _token_okay(text):
    """Decides whether the given token is a valid expandable query."""
    text = ''.join(c for c in text if 127 > ord(c) > 31)
    text = text.translate(Service.trans)
    if len(text) < 3 or Stopword.gql('WHERE token = :1', text).get() is not None:
        return False
    return True


service = Service()
