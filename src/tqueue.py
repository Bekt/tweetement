import logging
from service import service
import webapp2

from models import (Query, ExpandedQuery, Status)


class QueueHandler(webapp2.RequestHandler):

    def pop(self):
        """Pops a query from the queue and performs query expansion."""
        qid = int(self.request.get('qid'))
        result = Query.get_by_id(qid)
        if not result or result.status != Status.Pending:
            logging.warning('Query not pending. qid={}'.format(qid))
            return
        logging.info('Queue pop: {}'.format(qid))
        if not result.equery:
            equery = ExpandedQuery(qid=qid)
            equery.put()
            result.equery = equery.key.id()
        result.status = Status.Working
        result.put()
        try:
            expand_query(qid)
            result.status = Status.Done
        except Exception as e:
            logging.exception(e.message)
            result.status = Status.Cancelled
            result.status_msg = e.message
        finally:
            result.put()


def expand_query(qid):
    """Expand the given query.

    TODO(kanat): Clean this shit up.
    """
    result = Query.get_by_id(qid)
    basic_results = service.fetch(result.query, limit=100)

    hashtags = service.top_hashtags(basic_results, limit=2)
    keywords = service.top_keywords(basic_results, limit=2)

    h1 = service.fetch(hashtags[0], limit=4)
    h2 = service.fetch(hashtags[1], limit=4)

    k1 = service.fetch(keywords[0], limit=4)
    k2 = service.fetch(keywords[1], limit=4)

    equery = ExpandedQuery.get_by_id(result.equery)
    equery.hashtags = hashtags
    equery.keywords = keywords
    for r in basic_results:
        equery.basic_results.append(r.id)
    for r in h1:
        equery.hashtag_results.append(r.id)
    for r in h2:
        equery.hashtag_results.append(r.id)
    for r in k1:
        equery.keyword_results.append(r.id)
    for r in k2:
        equery.keyword_results.append(r.id)
    equery.put()
