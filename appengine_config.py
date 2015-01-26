import sys
import os.path

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))

# Workaround the dev-environment SSL:
#   http://stackoverflow.com/q/16192916/893652
if os.environ.get('SERVER_SOFTWARE', '').startswith('Development'):
    import imp
    import os
    from google.appengine.tools.devappserver2.python import sandbox

    sandbox._WHITE_LIST_C_MODULES += ['_ssl', '_socket']
    imp.load_source('socket',
                    os.path.join(os.path.dirname(os.__file__), 'socket.py'))
