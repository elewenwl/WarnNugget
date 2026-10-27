"""Validation shared by preference editors and the apply path."""
import re

BUNDLE_IDENTIFIER_PATTERN = r"(?:[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)?"


def valid_bundle_identifier(value):
    return (isinstance(value, str) and len(value) <= 255
            and re.fullmatch(BUNDLE_IDENTIFIER_PATTERN, value) is not None)

