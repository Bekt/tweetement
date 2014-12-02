import webapp2


app = webapp2.WSGIApplication([
    webapp2.Route(r'/api/echo', name='api_echo', methods=['GET'],
                 handler='controllers.ApiHandler:echo'),
], debug=True)
