"""Stable fixture identities and the public demonstration write policy."""

from uuid import NAMESPACE_URL, uuid5


def demo_id(key):
    return uuid5(NAMESPACE_URL, "talenthub:v2:demo:" + key)


PUBLIC_READ_ONLY_IDS = frozenset(
    demo_id("user:" + key)
    for key in ("school", "school2", "company", "academy", "admin")
)


def preview_only(user):
    return user.id in PUBLIC_READ_ONLY_IDS


def demo_preview(endpoint):
    """Opt a write endpoint into its explicitly implemented preview behavior."""
    endpoint.demo_preview = True
    return endpoint
