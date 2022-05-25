"""
Test archivist
"""

from unittest import mock, TestCase

from archivist.archivist import Archivist
from archivist.constants import (
    EVENTS_LABEL,
    HEADERS_REQUEST_TOTAL_COUNT,
    HEADERS_TOTAL_COUNT,
    PUBLICASSETS_LABEL,
    PUBLICASSETS_SUBPATH,
    PUBLICASSETS_WILDCARD,
    ROOT,
)

from .testevents import (
    ASSET_ID,
    EVENT_ATTRS,
    PROPS,
    REQUEST,
    RESPONSE,
)
from .mock_response import MockResponse

# pylint: disable=protected-access


class TestPublicEvents(TestCase):
    """
    Test Archivist PublicEvents Create method
    """

    maxDiff = None

    def setUp(self):
        self.arch = Archivist("url", None, max_time=1)

    def tearDown(self):
        self.arch = None

    def test_publicevents_str(self):
        """
        Test events str
        """
        self.assertEqual(
            str(self.arch.publicevents),
            "PublicEventsClient(url)",
            msg="Incorrect str",
        )

    def test_public_events_create(self):
        """
        Test event creation
        """
        with mock.patch.object(self.arch._session, "post") as mock_post:
            mock_post.return_value = MockResponse(200, **RESPONSE)

            event = self.arch.publicevents.create(
                f"public{ASSET_ID}", PROPS, EVENT_ATTRS, confirm=False
            )
            args, kwargs = mock_post.call_args
            self.assertEqual(
                args,
                (
                    (
                        f"url/{ROOT}/{PUBLICASSETS_SUBPATH}"
                        f"/{PUBLICASSETS_LABEL}/xxxxxxxxxxxxxxxxxxxx"
                        f"/{EVENTS_LABEL}"
                    ),
                ),
                msg="CREATE method args called incorrectly",
            )
            self.assertEqual(
                kwargs,
                {
                    "headers": {},
                    "json": REQUEST,
                    "verify": True,
                },
                msg="CREATE method kwargs called incorrectly",
            )
            self.assertEqual(
                event,
                RESPONSE,
                msg="CREATE method called incorrectly",
            )

    def test_publicevents_count(self):
        """
        Test event counting
        """
        with mock.patch.object(self.arch._session, "get") as mock_get:
            mock_get.return_value = MockResponse(
                200,
                headers={HEADERS_TOTAL_COUNT: 1},
                events=[
                    RESPONSE,
                ],
            )

            count = self.arch.publicevents.count(asset_id=ASSET_ID)
            self.assertEqual(
                count,
                1,
                msg="Incorrect count",
            )
            self.assertEqual(
                tuple(mock_get.call_args),
                (
                    (
                        (
                            f"url/{ROOT}/{PUBLICASSETS_SUBPATH}"
                            f"/{PUBLICASSETS_LABEL}/xxxxxxxxxxxxxxxxxxxx"
                            f"/{EVENTS_LABEL}"
                        ),
                    ),
                    {
                        "headers": {
                            HEADERS_REQUEST_TOTAL_COUNT: "true",
                        },
                        "params": {"page_size": 1},
                        "verify": True,
                    },
                ),
                msg="GET method called incorrectly",
            )

    def test_publicevents_count_with_wildcard_asset(self):
        """
        Test event counting

        NOTE: this test will fail upstream with a 4xx error
        """
        with mock.patch.object(self.arch._session, "get") as mock_get:
            mock_get.return_value = MockResponse(
                200,
                headers={HEADERS_TOTAL_COUNT: 1},
                events=[
                    RESPONSE,
                ],
            )

            _ = self.arch.publicevents.count(
                attrs={"arc_firmware_version": "1.0"},
            )
            self.assertEqual(
                tuple(mock_get.call_args),
                (
                    (
                        (
                            f"url/{ROOT}/{PUBLICASSETS_SUBPATH}"
                            f"/{PUBLICASSETS_WILDCARD}"
                            f"/{EVENTS_LABEL}"
                        ),
                    ),
                    {
                        "headers": {
                            HEADERS_REQUEST_TOTAL_COUNT: "true",
                        },
                        "params": {
                            "page_size": 1,
                            "event_attributes.arc_firmware_version": "1.0",
                        },
                        "verify": True,
                    },
                ),
                msg="GET method called incorrectly",
            )
