import json
import logging
import os
import re
from functools import wraps, lru_cache
from typing import Dict, Any, Callable

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
    @wraps(api_method)
    def method_wrapper(
            *args, response_update: Dict[str, Any] = None, **kwargs
    ) -> BaseResponse:
        # get url from args/kwargs
        relative_url = args[0]
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
            except KeyError:
                LOGGER.warning(
                    f'There are no known example responses for HTTP status {response_status}, '
                    f'using empty response. You may want to provide a full json response '
                    f'using the "json" keyword argument.'
                )
                response = {}

            # update fields if necessary
            if response_update is not None:
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
    def __getattribute__(self, name):
        attr = super().__getattribute__(name)
        if name in ['delete', 'get', 'head', 'options', 'patch', 'post', 'put']:
            return _api_method_adapter(attr)
        else:
            return attr
