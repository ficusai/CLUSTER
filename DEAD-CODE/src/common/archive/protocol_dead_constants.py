"""Archived dead constants previously defined in src/common/protocol.py.

None of these were referenced anywhere in the codebase. The deploy message
type was planned but never implemented.
"""

MAGIC = b"CLUSTER\x00\x01"
PROTO_VERSION = 1

MSG_DEPLOY = "deploy"
MSG_DEPLOY_ACK = "deploy_ack"