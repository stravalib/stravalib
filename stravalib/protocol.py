"""
Low-level classes for interacting directly with the Strava API webservers.
"""
from __future__ import division, absolute_import, print_function, unicode_literals
import abc
import os.path
import logging
import urlparse
import functools
from urllib import urlencode

import requests

from stravalib import exc

class ApiV3(object):
    """
    This class is responsible for performing the HTTP requests, rate limiting, and error handling.
    """
    __metaclass__ = abc.ABCMeta

    server = 'www.strava.com'
    api_base = '/api/v3'

    def __init__(self, access_token=None, requests_session=None, rate_limiter=None):
        """
        Initialize this protocol client, optionally providing a (shared) :class:`requests.Session`
        object.

        :param access_token: The token that provides access to a specific Strava account.
        :param requests_session: An existing :class:`requests.Session` object to use.
        """
        self.log = logging.getLogger('{0.__module__}.{0.__name__}'.format(self.__class__))
        self.access_token = access_token
        if requests_session:
            self.rsession = requests_session
        else:
            self.rsession = requests.Session()

        if rate_limiter is None:
            # Make it a dummy function, so we don't have to check if it's defined before
            # calling it later
            rate_limiter = lambda: None

        self.rate_limiter = rate_limiter

    def authorization_url(self, client_id, redirect_uri, approval_prompt='auto', scope=None, state=None):
        """
        Get the URL needed to authorize your application to access a Strava user's information.

        See http://strava.github.io/api/v3/oauth/

        :param client_id: The numeric developer client id.
        :type client_id: int

        :param redirect_uri: The URL that Strava will redirect to after successful (or failed) authorization.
        :type redirect_uri: str

        :param approval_prompt: Whether to prompt for approval even if approval already granted to app.
                                Choices are 'auto' or 'force'.  (Default is 'auto')
        :type approval_prompt: str

        :param scope: The access scope required.  Omit to imply "public".  Valid values are 'public', 'write', 'view_private', 'view_private,write'
        :type scope: str

        :param state: An arbitrary variable that will be returned to your application in the redirect URI.
        :type state: str

        :return: The URL to use for authorization link.
        :rtype: str
        """
        assert approval_prompt in ('auto', 'force')
        if isinstance(scope, (list, tuple)):
            scope = ','.join(scope)
        params = {'client_id': client_id,
                  'redirect_uri': redirect_uri,
                  'approval_prompt': approval_prompt,
                  'response_type': 'code'}
        if scope is not None:
            params['scope'] = scope
        if state is not None:
            params['state'] = state

        return urlparse.urlunsplit(('https', self.server, '/oauth/authorize', urlencode(params), ''))

    def exchange_code_for_token(self, client_id, client_secret, code):
        """
        Exchange the temporary authorization code (returned with redirect from strava authorization URL)
        for a permanent access token.

        :param client_id: The numeric developer client id.
        :type client_id: int

        :param client_secret: The developer client secret
        :type client_secret: str

        :param code: The temporary authorization code
        :type code: str

        :return: The access token.
        :rtype: str
        """
        response = self._request('https://{0}/oauth/token'.format(self.server),
                              params={'client_id': client_id, 'client_secret': client_secret, 'code': code},
                              method='POST')
        token = response['access_token']
        self.access_token = token
        return token

    def _resolve_url(self, url):
        if not url.startswith('http'):
            url = urlparse.urljoin('https://{0}'.format(self.server), self.api_base + '/' + url.strip('/'))
        return url

    def _request(self, url, params=None, files=None, method='GET', check_for_errors=True):

        url = self._resolve_url(url)
        self.log.info("{method} {url!r} with params {params!r}".format(method=method, url=url, params=params))
        if params is None:
            params = {}
        if self.access_token:
            params['access_token'] = self.access_token

        methods = {'GET': self.rsession.get,
                   'POST': functools.partial(self.rsession.post, files=files),
                   'PUT': self.rsession.put,
                   'DELETE': self.rsession.delete}

        try:
            requester = methods[method.upper()]
        except KeyError:
            raise ValueError("Invalid/unsupported request method specified: {0}".format(method))

        raw = requester(url, params=params)
        if check_for_errors:
            self._handle_protocol_error(raw)

        # 204 = No content
        if raw.status_code in [204,]:
            resp = []
        else:
            resp = raw.json()

        # TODO: We should parse the response to get the rate limit details and
        # update our rate limiter.
        # see: http://strava.github.io/api/#access

        # At this stage we should assume that request was successful and we should invoke
        # our rate limiter.  (Note that this may need to be reviewed; some failures may
        # also count toward the limit?)
        self.rate_limiter()

        return resp

    def _handle_protocol_error(self, response):
        """
        Parses the raw response from the server, raising a :class:`stravalib.exc.Fault` if the
        server returned an error.

        :param response: The response object.
        :raises Fault: If the response contains an error.
        """
        error_str = None
        try:
            json_response = response.json()
        except ValueError:
            pass
        else:
            if 'message' in json_response or 'errors' in json_response:
                error_str = '{0}: {1}'.format(json_response.get('message', 'Undefined error'), json_response.get('errors'))

        x = None
        if 400 <= response.status_code < 500:
            x = requests.exceptions.HTTPError('%s Client Error: %s [%s]' % (response.status_code, response.reason, error_str))
        elif 500 <= response.status_code < 600:
            x = requests.exceptions.HTTPError('%s Server Error: %s [%s]' % (response.status_code, response.reason, error_str))
        elif error_str:
            x = exc.Fault(error_str)

        if x is not None:
            raise x

        return response

    def _extract_referenced_vars(self, s):
        """
        Utility method to find the referenced format variables in a string.
        (Assumes string.format() format vars.)
        :param s: The string that contains format variables. (e.g. "{foo}-text")
        :return: The list of referenced variable names. (e.g. ['foo'])
        :rtype: list
        """
        d = {}
        while True:
            try:
                s.format(**d)
            except KeyError as exc:
                # exc.args[0] contains the name of the key that was not found;
                # 0 is used because it appears to work with all types of placeholders.
                d[exc.args[0]] = 0
            else:
                break
        return d.keys()

    def get(self, url, check_for_errors=True, **kwargs):
        """
        Performs a generic GET request for specified params, returning the response.
        """
        referenced = self._extract_referenced_vars(url)
        url = url.format(**kwargs)
        params = dict([(k,v) for k,v in kwargs.items() if not k in referenced])
        return self._request(url, params=params, check_for_errors=check_for_errors)

    def post(self, url, files=None, check_for_errors=True, **kwargs):
        """
        Performs a generic POST request for specified params, returning the response.
        """
        referenced = self._extract_referenced_vars(url)
        url = url.format(**kwargs)
        params = dict([(k,v) for k,v in kwargs.items() if not k in referenced])
        return self._request(url, params=params, files=files, method='POST', check_for_errors=check_for_errors)

    def put(self, url, check_for_errors=True, **kwargs):
        """
        Performs a generic PUT request for specified params, returning the response.
        """
        referenced = self._extract_referenced_vars(url)
        url = url.format(**kwargs)
        params = dict([(k,v) for k,v in kwargs.items() if not k in referenced])
        return self._request(url, params=params, method='PUT', check_for_errors=check_for_errors)