from google.appengine.ext import ndb
from google.appengine.ext.ndb import msgprop
from protorpc import messages


class Status(messages.Enum):
    """Query status."""
    Pending = 0
    Working = 1
    Done = 2
    Cancelled = 3


class Method(ndb.Model):
    """Experiment method."""
    qid = ndb.IntegerProperty()
    version = ndb.IntegerProperty()
    query = ndb.StringProperty()
    status_ids = ndb.IntegerProperty(repeated=True)


class Query(ndb.Model):
    """Query details."""
    query = ndb.StringProperty()
    uid = ndb.IntegerProperty()
    email = ndb.StringProperty(indexed=False)
    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True)
    status = msgprop.EnumProperty(Status, default=Status.Pending)
    status_msg = ndb.StringProperty(indexed=False)
    hashtags = ndb.StringProperty(repeated=True, indexed=False)
    keywords = ndb.StringProperty(repeated=True, indexed=False)
    methods = ndb.KeyProperty(kind=Method, repeated=True)


class Stopword(ndb.Model):
    token = ndb.StringProperty()


class Feedback(ndb.Model):
    """Feedback for a particular query.
        1: interesting, 0: neutral -1: not interesting.
    """
    qid = ndb.IntegerProperty()
    uid = ndb.IntegerProperty()
    sid = ndb.IntegerProperty()
    score = ndb.IntegerProperty(indexed=False, choices=[-1, 0, 1])
