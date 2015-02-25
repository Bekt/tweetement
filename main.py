import credentials
import webapp2

config = {
    'webapp2_extras.sessions': {
        'cookie_name': '_simpleauth_sess',
        'secret_key': credentials.session_key
    },
    'webapp2_extras': {
        'user_attributes': []
    }
}


app = webapp2.WSGIApplication([
    webapp2.Route(r'/api/echo', name='echo', methods=['GET'],
                  handler='api_controller.ApiHandler:echo'),
    webapp2.Route(r'/api/enqueue', name='enqueue', methods=['POST'],
                  handler='api_controller.ApiHandler:enqueue'),
    webapp2.Route(r'/api/result', name='result', methods=['GET'],
                  handler='api_controller.ApiHandler:result'),
    webapp2.Route(r'/api/feedback', name='feedback', methods=['POST'],
                  handler='api_controller.ApiHandler:feedback'),
    webapp2.Route(r'/api/scores', name='scores', methods=['GET'],
                  handler='api_controller.ApiHandler:scores'),
    webapp2.Route(r'/api/latest', name='latest', methods=['GET'],
                  handler='api_controller.ApiHandler:latest'),

    webapp2.Route(r'/queue/pop', name='pop', methods=['POST'],
                  handler='tqueue.QueueHandler:pop'),

    webapp2.Route('/', name='home', methods=['GET'],
                  handler='auth_controller.PageHandler:index'),
    webapp2.Route('/logout', name='logout', methods=['GET'],
                  handler='auth_controller.AuthHandler:logout'),
    webapp2.Route('/auth/<provider>', name='auth_login',
                  handler='auth_controller.AuthHandler:_simple_auth'),
    webapp2.Route('/auth/<provider>/callback', name='auth_callback',
                  handler='auth_controller.AuthHandler:_auth_callback'),
], config=config, debug=True)
