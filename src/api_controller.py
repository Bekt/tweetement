import json
import logging
import random
import re
import webapp2

from auth_controller import BaseRequestHandler
from models import (Query, Status, Feedback)
from datetime import datetime
from google.appengine.api import taskqueue
from google.appengine.ext import ndb
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
        uid = self.user_session['user_id']
        result = _enqueue(self.auth_info, query=query, email=email, uid=uid)
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
        if result:
            self.write(result)
        else:
            self.write_error('Query doesn\'t exist.', 404)

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
            q = Query.get_by_id(qid)
            if q is None:
                raise ValueError()
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

    def latest(self):
        """Retrieves the latest queries."""
        queries = Query.gql('WHERE status = :1 ORDER BY updated DESC',
                            Status.Done).fetch(limit=10)
        qs = []
        for q in queries:
            d = q.to_dict(include=['query'])
            d['qid'] = q.key.id()
            qs.append(d)
        self.write({'items': qs})

    def write(self, response, status=200):
        """Writes a JSON response."""
        self.response.headers['Content-Type'] = 'application/json'
        self.response.set_status(status)
        self.response.out.write(json.dumps(json_encode(response)))

    def write_error(self, reason, status=400):
        """Writes a JSON response with error code and message."""
        self.write({'error_message': reason, 'status_code': status},
                   status=status)

    def handle_exception(self, exception, debug):
        """Handle and log exceptions."""
        logging.exception(exception)
        if isinstance(exception, webapp2.HTTPException):
            self.write_error(exception.message, exception.code)
        else:
            self.write_error('Uh-oh, something went wrong.', 500)


def _enqueue(auth_info, **kwargs):
    result = Query(**kwargs)
    result.put()
    taskqueue.add(url='/queue/pop', params={
        'qid': result.key.id(),
        'oauth_token': auth_info.get('oauth_token', ''),
        'oauth_token_secret': auth_info.get('oauth_token_secret', '')
    })
    return result


def _result(qid):
    result = Query.get_by_id(qid)
    if result is not None:
        d = result.to_dict(exclude={'email', 'uid'})
        d['qid'] = qid
        if result.status == Status.Done and result.methods:
            methods = ndb.get_multi(result.methods)
            tweets = set()
            for ind, m in enumerate(methods):
                # Note: should this be the first 5 or random 5?
                tweets.update(m.status_ids[:5])
            d['status_ids'] = list(tweets)
            random.shuffle(d['status_ids'])
        return d


def json_encode(obj):
    """Custom JSON encoder for types that aren't handled by default."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, messages.Enum):
        return obj.name
    if isinstance(obj, (int, long)) and obj >= (1 << 31):
        return str(obj)
    if isinstance(obj, ndb.Key):
        return str(obj.id())
    if isinstance(obj, dict):
        return {k: json_encode(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return map(json_encode, obj)
    return obj
