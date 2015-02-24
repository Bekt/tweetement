import json
import logging
import random
import re
import webapp2

from auth_controller import BaseRequestHandler
from models import (Query, ExpandedQuery, Status, Feedback)
from datetime import datetime
from google.appengine.api import taskqueue
from protorpc import messages

EMAIL_RE = re.compile(r'[^@]+@[^@]+\.[^@]+')


def login_required(func):
    """Decorator that throws an exception if user us not authorized."""
    def check_login(self, *args, **kwargs):
        if not self.user_session:
            self.abort(401, detail='Authorization required.')
        else:
            return func(self, *args, **kwargs)
    return check_login


class ApiHandler(BaseRequestHandler):
    """Request handler methods. Expects and returns JSON objects."""

    def echo(self):
        """Method that returns echoes the given message."""
        msg = self.request.get('message', '')
        response = {'message': msg * 2}
        self.write(response)

    @login_required
    def enqueue(self):
        """Puts a new query in the queue."""
        req = json.loads(self.request.body)
        query = req.get('query', '').strip()
        email = req.get('email', '').strip()
        if not query.strip() or query.isdigit():
            self.abort(400, detail='Please specify a valid query.')
        if email and EMAIL_RE.match(email) is None:
            self.abort(400, detail='Please specify a valid email.')
        logging.info('Enqueue: {}'.format(query))
        result = _enqueue(self.auth_info, query=query, email=email)
        self.write({'qid': result.key.id()})

    @login_required
    def result(self):
        """Retrieves details about the given query."""
        qid = self.request.get('qid', '')
        if not qid or not qid.isdigit():
            self.abort(400, detail='Please provide a valid query ID.')
        qid = int(qid)
        logging.info('Result: {}'.format(qid))
        result = _result(qid)
        self.write(result)

    @login_required
    def feedback(self):
        """Provide a feedback for a status.

        Overrides the older feedback if there was any.
        """
        req = json.loads(self.request.body)
        try:
            qid = int(req.get('qid', ''))
            sid = int(req.get('sid', ''))
            score = int(req.get('score', ''))
            if score < -1 or score > 1:
                self.abort(400, detail='Invalid score.')
            uid = self.user_session['user_id']
            f = Feedback.gql('WHERE uid = :1 AND qid = :2 AND sid = :3',
                             uid, qid, sid).get()
            if f is None:
                f = Feedback(uid=uid, qid=qid, sid=sid)
            f.score = score
            f.put()
            self.write({'message': 'success'})
        except ValueError:
            self.abort(400,
                       detail='Please specify valid query ID and status ID.')

    @login_required
    def scores(self):
        """Retrieves previously provided feedback for a query."""
        qid = int(self.request.get('qid'))
        uid = self.user_session['user_id']
        fs = Feedback.gql('WHERE uid = :1 AND qid = :2', uid, qid).fetch()
        self.write({'items': [f.to_dict() for f in fs]})

    def write(self, response, status=200):
        """Writes a JSON response."""
        self.response.headers['Content-Type'] = 'application/json'
        self.response.set_status(status)
        self.response.out.write(json.dumps(json_encode(response)))

    def write_error(self, reason, status=400):
        """Writes a JSON response with error code and message."""
        self.write({'error_message': reason,
                    'status_code': status}, status=400)

    def handle_exception(self, exception, debug):
        """Handle and log exceptions."""
        logging.exception(exception)
        if isinstance(exception, webapp2.HTTPException):
            self.write_error(exception.message, exception.code)
        else:
            self.write_error('Uh-ok, something went wrong.', 500)


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
            d['status_ids'] = list(tweets)
            d['expanded_query'] = equery.to_dict()
        return d


def json_encode(obj):
    """Custom JSON encoder for types that aren't handled by default."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, messages.Enum):
        return obj.name
    if isinstance(obj, (int, long)) and obj >= (1 << 31):
        return str(obj)
    if isinstance(obj, dict):
        return {k: json_encode(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return map(json_encode, obj)
    return obj