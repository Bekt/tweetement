import credentials
import logging
import webapp2

from webapp2_extras import (auth, sessions, jinja2)
from simpleauth import SimpleAuthHandler


class BaseRequestHandler(webapp2.RequestHandler):
    """This class is mostly copy-paste from
            https://github.com/crhym3/simpleauth/blob/master/example/handlers.py
    """

    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)
        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def jinja2(self):
        """Returns a Jinja2 renderer cached in the app registry."""
        return jinja2.get_jinja2(app=self.app)

    @webapp2.cached_property
    def session(self):
        """Returns a session using the default cookie key."""
        return self.session_store.get_session()

    @webapp2.cached_property
    def auth(self):
        return auth.get_auth()

    @webapp2.cached_property
    def current_user(self):
        """Returns currently logged in user."""
        user_dict = self.auth.get_user_by_session()
        if user_dict:
            return self.auth.store.user_model.get_by_id(user_dict['user_id'])

    @webapp2.cached_property
    def user_session(self):
        """Returns the user session dictionary."""
        return self.auth.get_user_by_session()

    @webapp2.cached_property
    def auth_info(self):
        """Return's oauth info."""
        return self.session.get('auth_info')

    @webapp2.cached_property
    def logged_in(self):
        """Returns true if a user is currently logged in, false otherwise."""
        return self.auth.get_user_by_session() is not None

    def render(self, template_name, template_vars={}):
        # Preset values for the template.
        v = {
            'user': self.current_user if self.logged_in else None
        }

        # Add manually supplied template values.
        v.update(template_vars)

        self.response.write(self.jinja2.render_template(template_name, **v))


class AuthHandler(BaseRequestHandler, SimpleAuthHandler):
    """Authentication handler for OAuth 2.0, 1.0(a) and OpenID."""

    USER_ATTRS = {
        'twitter': {
            'profile_image_url': 'avatar_url',
            'screen_name': 'name',
            'link': 'link'
        },
    }

    def _on_signin(self, data, auth_info, provider, extra=None):
        """Callback whenever a new or existing user is logging in.
         data is a user info dictionary.
         auth_info contains access token or oauth token and secret.
         extra is a dict with additional params passed to the auth init handler.
        """
        auth_id = '%s:%s' % (provider, data['id'])

        user = self.auth.store.user_model.get_by_auth_id(auth_id)
        _attrs = self._to_user_model_attrs(data, self.USER_ATTRS[provider])

        if user:
            user.populate(**_attrs)
            user.put()
            self.auth.set_session(self.auth.store.user_to_dict(user))
        else:
            if self.logged_in:
                u = self.current_user
                u.populate(**_attrs)
                u.add_auth_id(auth_id)
            else:
                ok, user = self.auth.store.user_model.create_user(auth_id, **_attrs)
                if ok:
                    self.auth.set_session(self.auth.store.user_to_dict(user))
                else:
                    return self.redirect('/')

        # Store OAuth tokens in session.
        self.session['auth_info'] = auth_info

        return self.redirect('/')

    def logout(self):
        self.session.pop('auth_info', None)
        self.auth.unset_session()
        self.redirect('/')

    def _callback_uri_for(self, provider):
        return self.uri_for('auth_callback', provider=provider, _full=True)

    def _get_consumer_info_for(self, provider):
        """Returns a tuple (key, secret) for auth init requests."""
        return credentials.auth_config[provider]

    def _get_optional_params_for(self, provider):
        """Returns optional parameters for auth init requests."""
        return credentials.auth_optional_params.get(provider)

    def _to_user_model_attrs(self, data, attrs_map):
        """Get the needed information from the provider dataset."""
        user_attrs = {}
        for k, v in attrs_map.iteritems():
            attr = (v, data.get(k)) if isinstance(v, str) else v(data.get(k))
            user_attrs.setdefault(*attr)
        return user_attrs


class PageHandler(BaseRequestHandler):

    def index(self):
        """Index page."""
        self.render('index.html')