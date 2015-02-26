import logging
import service
import webapp2

from models import (Query, Status, Method)
from collections import Counter
from google.appengine.api import mail
from google.appengine.ext import ndb


class QueueHandler(webapp2.RequestHandler):

    def pop(self):
        """Pops a query from the queue and performs query expansion."""
        qid = int(self.request.get('qid'))
        auth_info = (self.request.get('oauth_token'),
                     self.request.get('oauth_token_secret'))
        result = Query.get_by_id(qid)
        if not result or result.status != Status.Pending:
            logging.warning('Query not pending. qid={}'.format(qid))
            return
        logging.info('Queue pop: {}'.format(qid))
        result.status = Status.Working
        result.put()
        try:
            expand_query(qid, auth_info)
            result.status = Status.Done
        except Exception as e:
            logging.exception(e.message)
            result.status = Status.Cancelled
            result.status_msg = e.message
        result.put()
        if result.status == Status.Done:
            notify(qid)


def expand_query(qid, auth_info):
    """Expand the given query.

    TODO(kanat): Clean this shit up.
    """
    result = Query.get_by_id(qid)
    q = result.query
    serv = service.Service(auth_info[0], auth_info[1])
    tweets = serv.fetch(result.query, limit=195)
    hashtags = serv.top_hashtags(tweets, limit=10)
    keywords = serv.top_keywords(tweets, limit=10, exclude=set(q.split()))

    methods = []

    # Method-0: q
    if tweets:
        methods.append(Method(qid=qid, version=0, query=q,
                              status_ids=_extract_ids(tweets[:10])))
    # Method-1: q + h'
    if hashtags:
        q1 = q + ' ' + hashtags[0]
        m1 = serv.fetch(q1, limit=10)
        if m1:
            methods.append(Method(qid=qid, version=1, query=q1,
                                  status_ids=_extract_ids(m1)))
    # Method-2: q + k'
    if keywords:
        q2 = q + ' ' + keywords[0]
        m2 = serv.fetch(q2, limit=10)
        if m2:
            methods.append(Method(qid=qid, version=2, query=q2,
                                  status_ids=_extract_ids(m2)))
    # Method-3: q + h' + k'
    if hashtags and keywords:
        q3 = q + ' ' + hashtags[0] + ' ' + keywords[0]
        m3 = serv.fetch(q3, limit=10)
        if m3:
            methods.append(Method(qid=qid, version=3, query=q3,
                                  status_ids=_extract_ids(m3)))
    # Method-4: q + h' + h''
    if len(hashtags) > 1:
        q4 = q + ' ' + hashtags[0] + ' ' + hashtags[1]
        m4 = serv.fetch(q4, limit=10)
        if m4:
            methods.append(Method(qid=qid, version=4, query=q4,
                                  status_ids=_extract_ids(m4)))
    # Method-5: q + k' + k''
    if len(keywords) > 1:
        q5 = q + ' ' + keywords[0] + ' ' + keywords[1]
        m5 = serv.fetch(q5, limit=10)
        if m5:
            methods.append(Method(qid=qid, version=5, query=q5,
                                  status_ids=_extract_ids(m5)))
    # Method-6: (q + h' OR q + k') => sort by max-matching h and k
    if hashtags and keywords:
        q6 = '{} {} OR {} {}'.format(q, hashtags[0], q, keywords[0])
        m6 = serv.fetch(q6, limit=195)
        counter = Counter()
        for tweet in m6:
            for token in set(tweet.text.split()):
                ok, text = service._token_okay(token)
                if ok and (text in hashtags or text in keywords):
                    counter[tweet.id] += 1
        m6 = counter.most_common(10)
        if m6:
            methods.append(Method(qid=qid, version=6, query='q6',
                                  status_ids=[k for k, v in m6]))

    method_keys = ndb.put_multi(methods)
    result.hashtags = hashtags
    result.keywords = keywords
    result.methods = method_keys


def _extract_ids(tweets):
    return [t.id for t in tweets]


def notify(qid):
    result = Query.get_by_id(qid)
    if not result.email:
        return
    message = """
Expanded search results for "{query}" are available at {url}

Don't forget to provide feedback at the above URL.
"""
    try:
        url = 'http://tweetement.com/#/result/' + str(qid)
        body = message.format(query=result.query, url=url)
        mail.send_mail(sender='Tweetement <bekt17@gmail.com>',
                       to=result.email,
                       subject='Results for %s are ready' % result.query,
                       body=body)
    except Exception as e:
        # Oh well.
        logging.exception(e)
