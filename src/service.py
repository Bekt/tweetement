import logging
import string
import tweepy

from credentials import (consumer_key, consumer_secret)
from models import Stopword
from collections import Counter


class Service(object):

    # Map uppercase to lowercase, and deletes any punctuation.
    trans = {ord(string.ascii_uppercase[i]): ord(string.ascii_lowercase[i])
             for i in range(26)}
    trans.update({ord(c): None for c in string.punctuation})

    def __init__(self, access_token='', access_token_secret=''):
        self._tw_api = None
        self._access_token = access_token
        self._access_token_secret = access_token_secret

    @property
    def tw_api(self):
        """Tweepy API client."""
        if self._tw_api is None:
            auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
            auth.set_access_token(self._access_token, self._access_token_secret)
            self._tw_api = tweepy.API(auth)
        return self._tw_api

    def fetch(self, query, limit=100):
        """Fetches search results for the given query."""
        # Cursor doesn't work with dev_appserver.py :(
        # return list(tweepy.Cursor(self.tw_api.search, q=query, lang='en',
        #                          result_type='popular').items(limit))
        query += ' -filter:retweets'
        # Try to get as many 'popular' posts as possible.
        # Twitter limits this really hard.
        res_type = 'popular'
        last_id = -1
        tweets = []
        while len(tweets) < limit:
            count = limit - len(tweets)
            try:
                t = self.tw_api.search(q=query, count=count, result_type=res_type,
                                       lang='en', max_id=str(last_id - 1))
                if len(t) < 3 and res_type == 'popular':
                    tweets.extend(t)
                    res_type = 'mixed'
                    last_id = -1
                    continue
                if len(t) < 3 and res_type == 'mixed':
                    tweets.extend(t)
                    break
                tweets.extend(t)
                last_id = t[-1].id
            except tweepy.TweepError as e:
                logging.exception(e)
                break
        return tweets

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
    def top_keywords(tweets, limit=5, exclude=set()):
        """Extracts most frequent keywords from given tweets."""
        exc = set()
        for w in exclude:
            ok, text = _token_okay(w)
            if ok:
                exc.add(text)
        words = Counter()
        for t in tweets:
            for token in set(t.text.split()):
                ok, text = _token_okay(token)
                if ok and text not in exc:
                    words[text] += 1
        top = words.most_common(limit)
        return [t[0] for t in top]


def _token_okay(text):
    """Decides whether the given token is a valid expandable query."""
    text = ''.join(c for c in text if 127 > ord(c) > 31)
    try:
        text = text.translate(Service.trans)
    except TypeError:
        return False, text
    if (len(text) < 2 or text.isdigit()
            or Stopword.gql('WHERE token = :1', text).get() is not None):
        return False, text
    return True, text
