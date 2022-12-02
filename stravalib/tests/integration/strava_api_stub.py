import json
import logging
import os
import re
from functools import wraps, lru_cache
from typing import Dict, Any, Callable, Optional

import requests
from responses import BaseResponse, RequestsMock

from stravalib.protocol import ApiV3
from stravalib.tests import RESOURCES_DIR

LOGGER = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_strava_api_paths():
    use_local = False

    try:
        strava_api_swagger_response = requests.get(
            'https://developers.strava.com/swagger/swagger.json'
        )
        if strava_api_swagger_response.status_code != 200:
            use_local = True
    except requests.exceptions.ConnectionError:
        use_local = True

    if use_local:
        LOGGER.warning(
            'Failed to retrieve recent swagger API definition from Strava, using '
            '(potentially stale) version from local resources'
        )
        with open(os.path.join(RESOURCES_DIR, 'strava_swagger.json'), 'r') as swagger_file:
            return json.load(swagger_file)['paths']
    else:
        return strava_api_swagger_response.json()['paths']


def _api_method_adapter(api_method: Callable) -> Callable:
    """
    Decorator for mock registration methods of `responses.RequestsMock`
    """

    @wraps(api_method)
    def method_wrapper(
            *args,
            response_update: Dict[str, Any] = None,
            n_results: Optional[int] = None,
            **kwargs
    ) -> BaseResponse:
        """
        Wrapper for mock registration methods of `responses.RequestsMock`

        Parameters
        ----------
        response_update:
            Dict that will be used to update any JSON object defined as
            an example response in the API's swagger.json
        n_results:
            The number of example objects to be returned by the mock
            response (in case of an array response).
        *args:
            Url and/or other positional arguments that would otherwise
            be provided to the `responses` registration methods. Note
            that url is expected to be relative, matching one of the
            paths defined in the Strava API's swagger.json.
        **kwargs
            Keyword arguments that would otherwise be provided to the
            `responses` registration methods.

        Returns
        -------
        A mocked response registration object

        This wrapper expects a relative url that matches one of the
        paths in the swagger.json of Strava's API, e.g.,
        `/activities/{Id}`. For the given HTTP method and status code,
        the corresponding example JSON response is retrieved from the
        swagger.json, and used in the mock registration as the response
        body. This response can be updated with the optional
        `response_update` argument (e.g. to set specific fields). If
        the response is a JSON array, the `n_results` argument
        specifies how many objects are in the response.

        Alternatively, a complete response can be specified using the
        `json` or `body` keywords, as is usually done using the
        `responses` library. In that case, the response updating -
        and multiplication mechanisms above are ignored and the
        given response is returned as-is.
        """

        # get url from args/kwargs
        try:
            relative_url = args[0]
        except IndexError:
            try:
                relative_url = kwargs.pop('url')
            except KeyError:
                raise ValueError(
                    'Expecting url either as first positional argument or keyword argument'
                )
        # match url with swagger path
        path_info = _get_strava_api_paths()[relative_url]
        # find default response in swagger if no json response is provided in the kwargs
        if 'json' not in kwargs:
            http_method = api_method.args[0].lower()
            response_status = kwargs.get('status', 200)

            try:
                method_responses = path_info[http_method]
            except KeyError:
                raise ValueError(f'Endpoint {relative_url} has no support for method {http_method}')

            try:
                response = method_responses['responses'][str(response_status)]['examples']['application/json']
                if isinstance(response, list) and n_results is not None:
                    # Make sure response has n_results items
                    response = (response * (n_results // len(response) + 1))[:n_results]
                elif n_results is not None:
                    # Force single response in example into result list (not all examples provide lists)
                    LOGGER.warning(f'Forcing example single response into list')
                    response = [{**response, **response_update}] * n_results
            except KeyError:
                LOGGER.warning(
                    f'There are no known example responses for HTTP status {response_status}, '
                    f'using empty response. You may want to provide a full json response '
                    f'using the "json" keyword argument.'
                )
                response = {}

            # update fields if necessary
            if response_update is not None:
                if isinstance(response, list):
                    response = [{**item, **response_update} for item in response]
                else:
                    response.update(response_update)

            kwargs.update({'json': response})

        # replace named parameters in url by wildcards
        matching_url = re.sub(r'\{\w+\}', r'\\w+', relative_url)
        return api_method(
            re.compile(ApiV3().resolve_url(matching_url)),  # replaces url from args[0]
            *args[1:],
            **kwargs
        )
    return method_wrapper


class StravaAPIMock(RequestsMock):
    """
    A stub/mock for the Strava API.

    This is a thin wrapper around `responses.RequestsMock`. It
    intercepts calls for registering mock responses and replaces these
    by a decorated method that supports convenience arguments that are
    not in the `responses` package.

    The methods `delete`, `get`, `head`, `options`, `patch`, `post`,
    and `put` are intercepted (and decorated), while the generic method
    `add` can be used to bypass the decoration and directly use the
    `responses` API.
    """

    def __getattribute__(self, name):
        attr = super().__getattribute__(name)
        if name in ['delete', 'get', 'head', 'options', 'patch', 'post', 'put']:
            return _api_method_adapter(attr)
        else:
            return attr
