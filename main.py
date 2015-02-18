import webapp2


app = webapp2.WSGIApplication([
    webapp2.Route(r'/api/echo', name='echo', methods=['GET'],
                 handler='controllers.ApiHandler:echo'),
    webapp2.Route(r'/api/enqueue', name='enqueue', methods=['POST'],
                 handler='controllers.ApiHandler:enqueue'),
    webapp2.Route(r'/api/result', name='result', methods=['GET'],
                 handler='controllers.ApiHandler:result'),

    webapp2.Route(r'/queue/pop', name='pop', methods=['POST'],
                 handler='tqueue.QueueHandler:pop'),
], debug=True)
