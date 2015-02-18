from models import Stopword
from google.appengine.ext import ndb


stopwords = 'stoplist.txt'


def seed_stopwords():
    """Adds stop words from a file to the datastore."""
    with open(stopwords) as f:
        xs = []
        for word in f.read().splitlines():
            s = Stopword(token=word)
            xs.append(s)
        ndb.put_multi(xs)


def add_stopword(word):
    """Adds the given stop word to the datastore."""
    Stopword(token=word).put()
