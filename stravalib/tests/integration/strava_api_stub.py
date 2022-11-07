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
        # find default response in swagger
        response = path_info['get']['responses']['200']['examples']['application/json']
        # update fields if necessary
        response.update(response_update)
        # replace named parameters in url by wildcards
        matching_url = re.sub(r'\{\w+\}', r'\\w+', relative_url)
        return api_method(
            re.compile(ApiV3().resolve_url(matching_url)),
            *args[1:],
            json=response,
            **kwargs
        )
    return method_wrapper


class StravaAPIMock(RequestsMock):
    def __getattribute__(self, name):
        attr = super().__getattribute__(name)
        if name in ['add', 'delete', 'get', 'head', 'options', 'patch', 'post', 'put']:
            return _api_method_adapter(attr)
        else:
            return attr
