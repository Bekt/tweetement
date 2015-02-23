from models import Stopword
from google.appengine.ext import ndb


stopwords = 'stoplist.txt'


def seed_stopwords(flush=True):
    """Adds stop words from a file to the datastore."""
    if flush:
        ndb.delete_multi(Stopword.query().fetch(keys_only=True))
    with open(stopwords) as f:
        xs = []
        for word in f.read().splitlines():
            s = Stopword(token=word)
            xs.append(s)
        ndb.put_multi(xs)


def add_stopword(word):
    """Adds the given stop word to the datastore."""
    Stopword(token=word).put()
