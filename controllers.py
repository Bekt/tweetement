import json
import webapp2


class ApiHandler(webapp2.RequestHandler):

    def echo(self):
        msg = self.request.get('message', '')
        response = {'message': msg}
        self.write(response)

    def write(self, response):
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(response))
