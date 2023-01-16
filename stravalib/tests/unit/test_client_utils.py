import datetime
import os
from unittest import mock
from urllib import parse as urlparse

import pytz

from stravalib.client import Client
from stravalib.tests import RESOURCES_DIR, TestBase


class ClientUtilsTest(TestBase):
    client = Client()

    def test_utc_datetime_to_epoch_utc_datetime_given_correct_epoch_returned(
        self,
    ):
        dt = pytz.utc.localize(datetime.datetime(2014, 1, 1, 0, 0, 0))
        self.assertEqual(1388534400, self.client._utc_datetime_to_epoch(dt))


class ClientAuthorizationUrlTest(TestBase):
    client = Client()

    def get_url_param(self, url, key):
        """
        >>> get_url_param("http://www.example.com/?key=1", "key")
        1
        """
        return urlparse.parse_qs(urlparse.urlparse(url).query)[key][0]

    def test_incorrect_scope_raises(self):
        self.assertRaises(
            Exception,
            self.client.authorization_url,
            1,
            "www.example.com",
            scope="wrong",
        )
        self.assertRaises(
            Exception,
            self.client.authorization_url,
            1,
            "www.example.com",
            scope=["wrong"],
        )

    def test_correct_scope(self):
        url = self.client.authorization_url(
            1, "www.example.com", scope="activity:write"
        )
        self.assertEqual(self.get_url_param(url, "scope"), "activity:write")
        # Check also with two params
        url = self.client.authorization_url(
            1, "www.example.com", scope=["activity:write", "activity:read_all"]
        )
        self.assertEqual(
            self.get_url_param(url, "scope"),
            "activity:write,activity:read_all",
        )

    def test_scope_may_be_list(self):
        url = self.client.authorization_url(
            1, "www.example.com", scope=["activity:write", "activity:read_all"]
        )
        self.assertEqual(
            self.get_url_param(url, "scope"),
            "activity:write,activity:read_all",
        )

    def test_incorrect_approval_prompt_raises(self):
        self.assertRaises(
            Exception,
            self.client.authorization_url,
            1,
            "www.example.com",
            approval_prompt="wrong",
        )

    def test_state_param(self):
        url = self.client.authorization_url(
            1, "www.example.com", state="my_state"
        )
        self.assertEqual(self.get_url_param(url, "state"), "my_state")

    def test_params(self):
        url = self.client.authorization_url(1, "www.example.com")
        self.assertEqual(self.get_url_param(url, "client_id"), "1")
        self.assertEqual(
            self.get_url_param(url, "redirect_uri"), "www.example.com"
        )
        self.assertEqual(self.get_url_param(url, "approval_prompt"), "auto")


class TestClientUploadActivity(TestBase):
    client = Client()

    def test_upload_activity_file_with_different_types(self):
        """
        Test uploading an activity with different activity_file object types.

        """

        with mock.patch(
            "stravalib.protocol.ApiV3.post", return_value={}
        ), open(os.path.join(RESOURCES_DIR, "sample.tcx")) as fp:
            # test activity_file with type TextIOWrapper
            uploader = self.client.upload_activity(fp, data_type="tcx")
            self.assertTrue(uploader.is_processing)

            # test activity_file with type str
            uploader = self.client.upload_activity(
                fp.read(), data_type="tcx", activity_type="ride"
            )
            self.assertTrue(uploader.is_processing)

            # test activity_file with type bytes
            uploader = self.client.upload_activity(
                fp.read().encode("utf-8"),
                data_type="tcx",
                activity_type="ride",
            )
            self.assertTrue(uploader.is_processing)
