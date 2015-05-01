"""Commands to execute with interactive console.

A lot of these analysis were meant for one-time use only, so
the quality is poor. Most of these queries are very expensive.
"""

from google.appengine.ext import ndb
from models import Query, Feedback
from webapp2_extras.appengine.auth.models import User
from collections import defaultdict


def reindex_queries():
    """Reindexes Query entities to reflect new schema changes."""
    q = ndb.Query(kind='Query').fetch()
    ndb.put_multi(q)


def _user_queries(uid):
    """Returns queries submitted by a particular user."""
    user = User.get_by_id(uid)
    qs = Query.gql('WHERE uid = :1', user.key.id()).fetch()
    return {
        'user': user.name,
        'uid': user.key.id(),
        'queries': [{
            'query': q.query,
            'qid': q.key.id(),
            'feedback': [{
                'sid': f.sid,
                'score': f.score
            } for f in Feedback.gql('WHERE qid = :1', q.key.id())]
        } for q in qs]
    }


def user_queries(tw_handle):
    user_key = User.gql('WHERE name = :1', tw_handle).get(keys_only=True)
    return _user_queries(user_key.id())


def queries_by_user():
    """Return all queries, grouped by user."""
    user_keys = User.query().fetch(keys_only=True)
    return [_user_queries(k.id()) for k in user_keys]


def h():
    qs = ndb.Query(kind='Query').fetch()
    print('{} queries by {} users'.format(len(qs), len({q.uid for q in qs})))
    qual = []
    pick = {0,1,2,5,6}
    for q in qs:
        if len(q.hashtags) < 5 or len(q.keywords) < 5 or len(q.methods) < len(pick):
          continue
        ok = True
        ms = ndb.get_multi(q.methods)
        for p in pick:
          if not any(m.version == p for m in ms):
            ok = False
            break
        if not ok:
          continue
        for m in ms:
          if (len(m.status_ids) < 5 and m.version in pick):
            ok = False
            break
        if ok:
          qual.append(q)
    print('Qualified queries: {}'.format(len(qual)))
    # Filter out those that don't have enough feedback.
    excl = []
    for q in qual:
        total = set()
        for m in ndb.get_multi(q.methods):
            total.update(m.status_ids[:5])
        fc = Feedback.gql('WHERE uid = :1 AND qid = :2',
                          q.uid, q.key.id()).count()
        if fc != len(total):
            excl.append(q)
    qual =[q for q in qual if q not in excl]
    print('After filtering out by feedback: {}'.format(len(qual)))
    user_queries = defaultdict(list)
    for q in qual:
        user_queries[q.uid].append(q)
    for u in user_queries:
        user_queries[u] = user_queries[u][:3]
    qual = [q for qs in user_queries.values() for q in qs]
    print('After filtering by users: {} users with 3 queries max. Total: {}'
            .format(len(user_queries), len(qual)))
    return [q.key.id() for q in qual]


def print_queries(resp):
  for ind, r in enumerate(resp):
    q = Query.get_by_id(r)
    qs = [str(ind)]
    for m in ndb.get_multi(q.methods):
      if m.version != 6:
        qs.append(m.query)
    print(' & '.join(qs).replace('#', '\#') + ' \\\\')


def print_awp(resp):
    means = [0] * 7
    for ind, r in enumerate(resp):
      q = Query.get_by_id(r)
      qs = [str(ind)]
      for m in ndb.get_multi(q.methods):
        sc, bp = 0, 0.0
        wp = []
        for d in m.status_ids[:5]:
          score = Feedback.gql('WHERE uid = :1 AND qid = :2 AND sid = :3', q.uid, q.key.id(), d).get().score
          # +1 to work on a 0-2 scale.
          score += 1
          sc += score
          bp += 2.0
          wp.append(sc / bp)
        assert(len(wp) == 5)
        qs.append('{:.3f}'.format(sum(wp) / len(wp)))
        means[m.version] += (sum(wp) / len(wp))
      print(' & '.join(qs) + ' \\\\')

    print('')

    for me in means:
      print('{:.3f}'.format(me / len(resp)))


def print_originality(resp):
    means = [0] * 7
    for ind, r in enumerate(resp):
      q = Query.get_by_id(r)
      qs = [str(ind)]
      ms = ndb.get_multi(q.methods)
      ss = set(ms[0].status_ids[:5])
      for ind, m in enumerate(ms):
        if ind == 0:
          continue
        diff = set(m.status_ids[:5]).difference(ss)
        pct = len(diff) / 5.0
        qs.append('{:.2f}'.format(pct))
        means[m.version] += pct
      print(' & '.join(qs) + ' \\\\')

    print('')

    for me in means:
      print('{:.3f}'.format(me / len(resp)))
