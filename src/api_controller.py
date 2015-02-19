import json
import logging
import random
import re

from auth_controller import BaseRequestHandler
from models import (Query, ExpandedQuery, Status)
from datetime import datetime
from google.appengine.api import taskqueue
from protorpc import messages


EMAIL_RE = re.compile(r'[^@]+@[^@]+\.[^@]+')


class ApiHandler(BaseRequestHandler):
    """Request handler methods. Expects and returns JSON objects."""

    def echo(self):
        """Method that returns echoes the given message."""
        msg = self.request.get('message', '')
        response = {'message': msg * 2}
        self.write(response)

    def enqueue(self):
        """Puts a new query in the queue."""
        req = json.loads(self.request.body)
        query = req.get('query', '').strip()
        email = req.get('email', '').strip()
        if not query.strip() or query.isdigit():
            self.write_error('Please specify a valid query.')
            return
        if email and EMAIL_RE.match(email) is None:
            self.write_error('Please specify a valid email.')
            return
        logging.info('Enqueue: {}'.format(query))
        result = _enqueue(self.auth_info, query=query, email=email)
        self.write({'qid': result.key.id()})

    def result(self):
        """Retrieves details about the given query."""
        qid = self.request.get('qid', '')
        if not qid or not qid.isdigit():
            self.write_error('Please provide a valid query ID.')
            return
        qid = int(qid)
        logging.info('Result: {}'.format(qid))
        result = _result(qid)
        self.write(result)

    def write(self, response, status=200):
        """Writes a JSON response."""
        self.response.headers['Content-Type'] = 'application/json'
        self.response.set_status(status)
        self.response.out.write(json.dumps(response, default=_json_encoder))

    def write_error(self, reason):
        """Writes a JSON response with error code and message."""
        self.write({'error': reason}, status=400)


def _enqueue(auth_info, **kwargs):
    token, token_secret = ((auth_info['oauth_token'],
                           auth_info['oauth_token_secret'])
                           if auth_info is not None else ('', ''))
    result = Query(**kwargs)
    result.put()
    taskqueue.add(url='/queue/pop', params={
        'qid': result.key.id(),
        'oauth_token': token,
        'oauth_token_secret': token_secret,
    })
    return result


def _result(qid):
    result = Query.get_by_id(qid)
    if result is not None:
        d = result.to_dict()
        d['qid'] = qid
        if result.status == Status.Done:
            equery = ExpandedQuery.get_by_id(result.equery)
            tweets = set(random.sample(equery.basic_results,
                                       min(4, len(equery.basic_results))))
            tweets.update(random.sample(equery.hashtag_results,
                                        min(6, len(equery.hashtag_results))))
            tweets.update(random.sample(equery.keyword_results,
                                        min(6, len(equery.keyword_results))))
            d['status_ids'] = [str(t) for t in tweets]
            d['expanded_query'] = equery.to_dict()
        return d


def _json_encoder(obj):
    """Custom JSON encoder for types that aren't handled by default."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, messages.Enum):
        return obj.name
