from google.appengine.ext import ndb
from google.appengine.ext.ndb import msgprop
from protorpc import messages


class Status(messages.Enum):
    """Query status."""
    Pending = 0
    Working = 1
    Done = 2
    Cancelled = 3


class Query(ndb.Model):
    """Query details."""
    query = ndb.StringProperty()
    email = ndb.StringProperty(indexed=False)
    equery = ndb.IntegerProperty()
    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)
    status = msgprop.EnumProperty(Status, default=Status.Pending)
    status_msg = ndb.StringProperty()


class ExpandedQuery(ndb.Model):
    qid = ndb.IntegerProperty()
    # Tweet IDs from the original query.
    basic_results = ndb.IntegerProperty(repeated=True, indexed=False)
    # Expanded query: hashtags.
    hashtags = ndb.StringProperty(repeated=True)
    hashtag_results = ndb.IntegerProperty(repeated=True, indexed=False)
    # Expanded query: keywords.
    keywords = ndb.StringProperty(repeated=True)
    keyword_results = ndb.IntegerProperty(repeated=True, indexed=False)


class Stopword(ndb.Model):
    token = ndb.StringProperty()
