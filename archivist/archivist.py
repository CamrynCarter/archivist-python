# -*- coding: utf-8 -*-
"""Archivist connection interface

   This module contains the base Archivist class which manages
   the connection parameters to a RKVST instance and
   the basic REST verbs to GET, POST, PATCH and DELETE entities..

   The REST methods in this class should only be used directly when
   a CRUD endpoint for the specific type of entity is unavailable.
   Current CRUD endpoints are assets, events, locations, attachments.
   IAM subjects and IAM access policies.

   Instantiation of this class encapsulates the URL and authentication
   parameters (the max_time parameter is optional):

   .. code-block:: python

      with open(".auth_token", mode="r", encoding="utf-8") as tokenfile:
          authtoken = tokenfile.read().strip()

      # Initialize connection to Archivist
      arch = Archivist(
          "https://app.rkvst.io",
          authtoken,
          max_time=300.0,
      )

    The arch variable now has additional endpoints assets,events,locations,
    attachments, IAM subjects and IAM access policies documented elsewhere.

"""

from logging import getLogger
from copy import deepcopy
from time import time
from typing import BinaryIO, Dict, Optional, Union

from requests_toolbelt.multipart.encoder import MultipartEncoder

from .confirmer import MAX_TIME
from .constants import (
    ROOT,
    SEP,
)
from .dictmerge import _dotdict
from .errors import (
    _parse_response,
    ArchivistError,
)
from .archivistpublic import ArchivistPublic
from .retry429 import retry_429

from .access_policies import _AccessPoliciesClient
from .appidp import _AppIDPClient
from .applications import _ApplicationsClient
from .assets import _AssetsRestricted
from .assetattachments import _AssetAttachmentsClient
from .attachments import _AttachmentsClient
from .compliance import _ComplianceClient
from .compliance_policies import _CompliancePoliciesClient
from .composite import _CompositeClient
from .events import _EventsRestricted
from .locations import _LocationsClient
from .runner import _Runner
from .sboms import _SBOMSClient
from .subjects import _SubjectsClient
from .type_aliases import MachineAuth

LOGGER = getLogger(__name__)


class Archivist(ArchivistPublic):  # pylint: disable=too-many-instance-attributes
    """Base class for all Archivist endpoints.

    This class manages the connection to an Archivist instance and provides
    basic methods that represent the underlying REST interface.

    Args:
        url (str): URL of archivist endpoint
        auth: string representing JWT token.
        verify: if True the certificate is verified
        max_time (float): maximum time in seconds to wait for confirmation

    """

    # also change the type hints in __init__ below
    CLIENTS = {
        "access_policies": _AccessPoliciesClient,
        "assets": _AssetsRestricted,
        "assetattachments": _AssetAttachmentsClient,
        "appidp": _AppIDPClient,
        "applications": _ApplicationsClient,
        "attachments": _AttachmentsClient,
        "compliance": _ComplianceClient,
        "compliance_policies": _CompliancePoliciesClient,
        "composite": _CompositeClient,
        "events": _EventsRestricted,
        "locations": _LocationsClient,
        "runner": _Runner,
        "sboms": _SBOMSClient,
        "subjects": _SubjectsClient,
    }

    def __init__(
        self,
        url: str,
        auth: Union[None, str, MachineAuth],
        *,
        fixtures: Optional[Dict] = None,
        verify: bool = True,
        max_time: float = MAX_TIME,
    ):
        super().__init__(
            fixtures=fixtures,
            verify=verify,
            max_time=max_time,
        )

        if isinstance(auth, tuple):
            self._auth = None
            self._client_id = auth[0]
            self._client_secret = auth[1]
        else:
            self._auth = auth
            self._client_id = None
            self._client_secret = None

        self._expires_at = 0
        if url.endswith("/"):
            raise ArchivistError(f"URL {url} has trailing /")

        self._url = url
        self._root = SEP.join((url, ROOT))

        # Type hints for IDE autocomplete, keep in sync with CLIENTS map above
        self.access_policies: _AccessPoliciesClient
        self.appidp: _AppIDPClient
        self.applications: _ApplicationsClient
        self.assets: _AssetsRestricted
        self.assetattachments: _AssetAttachmentsClient
        self.attachments: _AttachmentsClient
        self.compliance: _ComplianceClient
        self.compliance_policies: _CompliancePoliciesClient
        self.composite: _CompositeClient
        self.events: _EventsRestricted
        self.locations: _LocationsClient
        self.runner: _Runner
        self.sboms: _SBOMSClient
        self.subjects: _SubjectsClient

    def __str__(self) -> str:
        return f"Archivist({self._url})"

    def __getattr__(self, value: str):
        """Create endpoints on demand"""
        LOGGER.debug("getattr %s", value)
        client = self.CLIENTS.get(value)

        if client is None:
            raise AttributeError

        c = client(self)
        super().__setattr__(value, c)
        return c

    @property
    def public(self) -> bool:
        """Not a public interface"""
        return False

    @property
    def url(self) -> str:
        """str: URL of Archivist endpoint"""
        return self._url

    @property
    def root(self) -> str:
        """str: ROOT of Archivist endpoint"""
        return self._root

    @property
    def auth(self) -> str:
        """str: authorization token."""
        if self._client_id is not None and self._expires_at < time():
            apptoken = self.appidp.token(self._client_id, self._client_secret)  # type: ignore
            self._auth = apptoken.get("access_token")
            if self._auth is None:
                raise ArchivistError("Auth token from client id,secret is invalid")
            self._expires_at = time() + apptoken["expires_in"] - 10  # fudge factor
            LOGGER.info("Refresh token")

        return self._auth  # type: ignore

    @property
    def Public(self):  # pylint: disable=invalid-name
        """Get a Public instance"""
        return ArchivistPublic(
            fixtures=deepcopy(self._fixtures),
            verify=self._verify,
            max_time=self._max_time,
        )

    def __copy__(self):
        return Archivist(
            self._url,
            self.auth,
            fixtures=deepcopy(self._fixtures),
            verify=self._verify,
            max_time=self._max_time,
        )

    def _add_headers(self, headers: Optional[Dict]) -> Dict:
        if headers is not None:
            newheaders = {**headers}
        else:
            newheaders = {}

        auth = self.auth  # this may trigger a refetch so only do it once here
        # for appidp endpoint there may not be an authtoken
        if auth is not None:
            newheaders["authorization"] = "Bearer " + auth.strip()

        return newheaders

    # currently only the archivist endpoint is allowed to create/modify data.
    # this may change...
    @retry_429
    def post(
        self,
        url: str,
        request: Optional[Dict],
        *,
        headers: Optional[Dict] = None,
        data: Optional[bool] = False,
    ) -> Dict:
        """POST method (REST)

        Creates an entity

        Args:
            url (str): e.g. v2/assets
            request (dict): request body defining the entity
            headers (dict): optional REST headers
            data (bool): send as form-encoded and not as json

        Returns:
            dict representing the response body (entity).
        """
        if data:
            response = self.session.post(
                url,
                data=request,
                verify=self.verify,
            )
        else:
            response = self.session.post(
                url,
                json=request,
                headers=self._add_headers(headers),
                verify=self.verify,
            )

        error = _parse_response(response)
        if error is not None:
            raise error

        return response.json()

    @retry_429
    def post_file(
        self,
        url: str,
        fd: BinaryIO,
        mtype: str,
        *,
        form: Optional[str] = "file",
        params: Optional[Dict] = None,
    ) -> Dict:
        """POST method (REST) - upload binary

        Uploads a file to an endpoint

        Args:
            url (str): e.g. v2/assets
            fd : iterable representing the contents of a file.
            mtype (str): mime type e.g. image/jpg
            params (dict): dictionary of optional path params

        Returns:
            dict representing the response body (entity).
        """
        multipart = MultipartEncoder(
            fields={
                form: ("filename", fd, mtype),
            }
        )
        headers = {
            "content-type": multipart.content_type,
        }

        response = self.session.post(
            url,
            data=multipart,  # type: ignore    https://github.com/requests/toolbelt/issues/312
            headers=self._add_headers(headers),
            verify=self.verify,
            params=_dotdict(params),
        )

        self._response_ring_buffer.appendleft(response)

        error = _parse_response(response)
        if error is not None:
            raise error

        return response.json()

    @retry_429
    def delete(self, url: str, *, headers: Optional[Dict] = None) -> Dict:
        """DELETE method (REST)

        Deletes an entity

        Args:
            url (str): e.g. v2/assets/xxxxxxxxxxxxxxxxxxxxxxxxxxxx`
            headers (dict): optional REST headers

        Returns:
            dict representing the response body (entity).
        """
        response = self.session.delete(
            url,
            headers=self._add_headers(headers),
            verify=self.verify,
        )

        self._response_ring_buffer.appendleft(response)

        error = _parse_response(response)
        if error is not None:
            raise error

        return response.json()

    @retry_429
    def patch(
        self,
        url: str,
        request: Dict,
        *,
        headers: Optional[Dict] = None,
    ) -> Dict:
        """PATCH method (REST)

        Updates the specified entity.

        Args:
            url (str): e.g. v2/assets/xxxxxxxxxxxxxxxxxxxxxxxxxxxx`
            request (dict): request body defining the entity changes.
            headers (dict): optional REST headers

        Returns:
            dict representing the response body (entity).
        """

        response = self.session.patch(
            url,
            json=request,
            headers=self._add_headers(headers),
            verify=self.verify,
        )

        self._response_ring_buffer.appendleft(response)

        error = _parse_response(response)
        if error is not None:
            raise error

        return response.json()
