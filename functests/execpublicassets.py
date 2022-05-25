"""
Test public assets creation
"""

from copy import deepcopy
from os import getenv
from json import dumps as json_dumps
from unittest import TestCase

from archivist.archivist import Archivist
from archivist.assets import BEHAVIOURS
from archivist.logger import set_logger
from archivist.proof_mechanism import ProofMechanism

# pylint: disable=fixme
# pylint: disable=missing-docstring
# pylint: disable=unused-variable


if getenv("TEST_DEBUG") is not None:
    set_logger(getenv("TEST_DEBUG"))

ATTRS = {
    "arc_firmware_version": "1.0",
    "arc_serial_number": "vtl-x4-07",
    "arc_description": "Traffic flow control light at A603 North East",
    "some_custom_attribute": "value",
}

ASSET_NAME = "Telephone with 2 attachments - one bad or not scanned 2022-03-01"
REQUEST_EXISTS_ATTACHMENTS = {
    "selector": [
        {
            "attributes": [
                "arc_display_name",
                "arc_namespace",
            ]
        },
    ],
    "behaviours": BEHAVIOURS,
    "proof_mechanism": ProofMechanism.SIMPLE_HASH.name,
    "attributes": {
        "arc_display_name": ASSET_NAME,
        "arc_namespace": "namespace",
        "arc_firmware_version": "1.0",
        "arc_serial_number": "vtl-x4-07",
        "arc_description": "Traffic flow control light at A603 North East",
        "arc_display_type": "Traffic light with violation camera",
        "some_custom_attribute": "value",
    },
    "public": True,
}


class TestPublicAssetCreate(TestCase):
    """
    Test Archivist Public Asset Create method
    """

    maxDiff = None

    def setUp(self):
        self.arch = Archivist(
            getenv("TEST_ARCHIVIST"), None, verify=False, max_time=300
        )
        self.attrs = deepcopy(ATTRS)
        self.traffic_light = deepcopy(ATTRS)
        self.traffic_light["arc_display_type"] = "Traffic light with violation camera"

    def tearDown(self):
        self.arch = None
        self.attrs = None
        self.traffic_light = None

    def test_public_asset_create_simple_hash(self):
        """
        Test asset creation uses simple hash proof mechanism
        """
        asset = self.arch.assets.create(
            attrs=self.traffic_light,
            props={
                "public": True,
            },
            confirm=True,
        )
        self.assertEqual(
            asset["proof_mechanism"],
            ProofMechanism.SIMPLE_HASH.name,
            msg="Incorrect asset proof mechanism",
        )

    def test_public_asset_create_khipu(self):
        """
        Test public asset creation using khipu proof mechanism
        """
        asset = self.arch.assets.create(
            props={
                "proof_mechanism": ProofMechanism.KHIPU.name,
                "public": True,
            },
            attrs=self.traffic_light,
        )
        print("asset", json_dumps(asset, sort_keys=True, indent=4))
        self.assertEqual(
            asset["proof_mechanism"],
            ProofMechanism.KHIPU.name,
            msg="Incorrect asset proof mechanism",
        )
        events = self.arch.publicevents.list(asset_id=asset["identity"])
        print("events", json_dumps(list(events), sort_keys=True, indent=4))
        asset = self.arch.assets.wait_for_confirmation(asset["identity"])
        print("asset", json_dumps(asset, sort_keys=True, indent=4))
        events = self.arch.publicevents.list(asset_id=asset["identity"])
        print("events", json_dumps(list(events), sort_keys=True, indent=4))

    def test_public_asset_create_event(self):
        """
        Test list
        """
        # get identity of first asset
        identity = None
        for asset in self.arch.assets.list():
            print("asset", json_dumps(asset, sort_keys=True, indent=4))
            identity = asset["identity"]
            break

        self.assertIsNotNone(
            identity,
            msg="Identity is None",
        )

        # different behaviours are also different.
        props = {
            "operation": "Record",
            # This event is used to record evidence.
            "behaviour": "RecordEvidence",
            # Optional Client-claimed time at which the maintenance was performed
            "timestamp_declared": "2019-11-27T14:44:19Z",
            # Optional Client-claimed identity of person performing the operation
            "principal_declared": {
                "issuer": "idp.synsation.io/1234",
                "subject": "phil.b",
                "email": "phil.b@synsation.io",
            },
        }
        attrs = {
            # Required Details of the RecordEvidence request
            "arc_description": "Safety conformance approved for version 1.6.",
            # Required The evidence to be retained in the asset history
            "arc_evidence": "DVA Conformance Report attached",
            # Example Client can add any additional information in further attributes,
            # including free text or attachments
            "conformance_report": "blobs/e2a1d16c-03cd-45a1-8cd0-690831df1273",
        }

        event = self.arch.publicevents.create(
            f"public{identity}", props=props, attrs=attrs, confirm=True
        )
        print("event", json_dumps(event, sort_keys=True, indent=4))
