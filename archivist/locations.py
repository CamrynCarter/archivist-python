"""Locations interface

   Direct access to the locations endpoint.

   The user is not expected to use this class directly. It is an attribute of the
   :class:`Archivist` class.

   For example instantiate an Archivist instance and execute the methods of the class:

   .. code-block:: python

      with open(".auth_token", mode="r", encoding="utf-8") as tokenfile:
          authtoken = tokenfile.read().strip()

      # Initialize connection to Archivist
      arch = Archivist(
          "https://app.rkvst.io",
          authtoken,
      )
      location = arch.locations.create(...)


"""

from copy import deepcopy
from logging import getLogger
from typing import Dict, Optional, Tuple

# pylint:disable=cyclic-import      # but pylint doesn't understand this feature
from . import archivist as type_helper  # pylint:disable=unused-import

from .constants import LOCATIONS_SUBPATH, LOCATIONS_LABEL
from .dictmerge import _deepmerge
from .errors import ArchivistNotFoundError
from .utils import selector_signature
from .type_aliases import NoneOnError


LOGGER = getLogger(__name__)


class Location(dict):
    """Location

    Location object has dictionary attributes.

    """

    @property
    def name(self) -> NoneOnError[str]:
        """str: name of the location"""
        name = None
        try:
            name = self["display_name"]
        except KeyError:
            pass

        return name


class _LocationsClient:
    """LocationsClient

    Access to locations entities using CRUD interface. This class is usually
    accessed as an attribute of the Archivist class.

    Args:
        archivist (Archivist): :class:`Archivist` instance

    """

    def __init__(self, archivist: "type_helper.Archivist"):
        self._archivist = archivist
        self._subpath = f"{archivist.root}/{LOCATIONS_SUBPATH}"
        self._label = f"{self._subpath}/{LOCATIONS_LABEL}"

    def __str__(self) -> str:
        return f"LocationsClient({self._archivist.url})"

    def create(self, props: Dict, *, attrs: Optional[Dict] = None) -> Location:
        """Create location

        Creates location with defined properties and attributes.

        Args:
            props (dict): properties for this location.
            attrs (dict): attributes of created location.

        Returns:
            :class:`Location` instance

        """
        LOGGER.debug("Create Location %s", props)
        return self.create_from_data(self.__params(props, attrs))

    def create_from_data(self, data: Dict) -> Location:
        """Create location

        Creates location with request body from data stream.
        Suitable for reading data from a file using json.load or yaml.load

        Args:
            data (dict): request body of location.

        Returns:
            :class:`Location` instance

        """
        return Location(**self._archivist.post(self._label, data))

    def create_if_not_exists(self, data: Dict) -> Tuple[Optional[Location], bool]:
        """
        Create a location if not already exists

        Args:
            data (dict): request body of location.

        A YAML representation of the data argument would be:

            .. code-block:: yaml

                selector:
                  - display_name
                  - attributes:
                    - wavestone_ext
                display_name: Apartements du Gare du Nord
                description: Residential apartment building in new complex above GdN station
                latitude: 48.8809
                longitude: 2.3553
                attributes:
                  address: 18 Rue de Dunkerque, 75010 Paris, France
                  wavestone_ext: managed

            The 'selector' setting is required.

        Returns:
            tuple of :class:`Location` instance, Boolean True if already exists

        """
        location = None
        data = deepcopy(data)
        selector = data.pop("selector")  # must exist
        props, attrs = selector_signature(selector, data)
        try:
            location = self.read_by_signature(props=props, attrs=attrs)

        except ArchivistNotFoundError:
            LOGGER.info(
                "location with selector %s,%s does not exist - creating", props, attrs
            )

        else:
            LOGGER.info("location with selector %s,%s already exists", props, attrs)
            return location, True

        return self.create_from_data(data), False

    def read(self, identity: str) -> Location:
        """Read location

        Reads location.

        Args:
            identity (str): location identity e.g. locations/xxxxxxxxxxxxxxxxxxxxxxx

        Returns:
            :class:`Location` instance

        """
        return Location(**self._archivist.get(f"{self._subpath}/{identity}"))

    def __params(self, props: Optional[Dict], attrs: Optional[Dict]) -> Dict:
        params = deepcopy(props) if props else {}
        if attrs:
            params["attributes"] = attrs

        return _deepmerge(self._archivist.fixtures.get(LOCATIONS_LABEL), params)

    def count(
        self, *, props: Optional[Dict] = None, attrs: Optional[Dict] = None
    ) -> int:
        """Count locations.

        Counts number of locations that match criteria.

        Args:
            props (dict): e.g. {"display_name": "Macclesfield" }
            attrs (dict): e.g. {"director": "john smith" }

        Returns:
            integer count of locations.

        """
        return self._archivist.count(self._label, params=self.__params(props, attrs))

    def list(
        self,
        *,
        page_size: Optional[int] = None,
        props: Optional[Dict] = None,
        attrs: Optional[Dict] = None,
    ):
        """List locations.

        Lists locations that match criteria.

        Args:
            props (dict): optional e.g. {"display_name": "Macclesfield" }
            attrs (dict): optional e.g. {"director": "john smith" }
            page_size (int): optional page size. (Rarely used)

        Returns:
            iterable that returns :class:`Location` instances

        """

        return (
            Location(**a)
            for a in self._archivist.list(
                self._label,
                LOCATIONS_LABEL,
                page_size=page_size,
                params=self.__params(props, attrs),
            )
        )

    def read_by_signature(
        self, *, props: Optional[Dict] = None, attrs: Optional[Dict] = None
    ) -> Location:
        """Read location by signature.

        Reads location that meets criteria. Only one location is expected.

        Args:
            props (dict): e.g. {"display_name": "Macclesfield" }
            attrs (dict): e.g. {"director": "john smith" }

        Returns:
            :class:`Location` instance

        """
        return Location(
            **self._archivist.get_by_signature(
                self._label,
                LOCATIONS_LABEL,
                params=self.__params(props, attrs),
            )
        )
