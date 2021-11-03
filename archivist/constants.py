"""Archivist constants

"""

# these are in separate file to stop import loops
ROOT = "archivist"
SEP = "/"

# define in MIME canonical form
HEADERS_REQUEST_TOTAL_COUNT = "X-Request-Total-Count"
HEADERS_TOTAL_COUNT = "X-Total-Count"
HEADERS_RETRY_AFTER = "Archivist-Rate-Limit-Reset"

CONFIRMATION_STATUS = "confirmation_status"
CONFIRMATION_PENDING = "PENDING"
CONFIRMATION_FAILED = "FAILED"
CONFIRMATION_CONFIRMED = "CONFIRMED"

ASSETS_SUBPATH = "v2"
ASSETS_LABEL = "assets"
ASSETS_WILDCARD = "assets/-"
EVENTS_LABEL = "events"

LOCATIONS_SUBPATH = "v2"
LOCATIONS_LABEL = "locations"

ATTACHMENTS_SUBPATH = "v1"
ATTACHMENTS_LABEL = "blobs"

ACCESS_POLICIES_SUBPATH = "iam/v1"
ACCESS_POLICIES_LABEL = "access_policies"

COMPLIANCE_SUBPATH = "v1"
COMPLIANCE_LABEL = "compliance"

COMPLIANCE_POLICIES_SUBPATH = "v1"
COMPLIANCE_POLICIES_LABEL = "compliance_policies"

SUBJECTS_SUBPATH = "iam/v1"
SUBJECTS_LABEL = "subjects"
