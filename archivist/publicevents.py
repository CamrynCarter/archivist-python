"""Events interface

   Direct access to the events endpoint.

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
      asset = arch.assets.create(...public=True)
      event = arch.publicevents.create(asset['identity'], ...)

"""

from logging import getLogger

from .constants import (
    PUBLICASSETS_SUBPATH,
    PUBLICASSETS_WILDCARD,
)
from .events import _EventsClient


LOGGER = getLogger(__name__)


class _PublicEventsClient(_EventsClient):
    """PublicEventsClient

    Access to events entities using the CRUD interface. This class is usually
    accessed as an attribute of the Archivist class.

    Args:
        archivist (Archivist): :class:`Archivist` instance

    """

    SUBPATH = PUBLICASSETS_SUBPATH
    WILDCARD = PUBLICASSETS_WILDCARD
    PREFIX = "public"

    def __str__(self) -> str:
        return f"PublicEventsClient({self._archivist.url})"
