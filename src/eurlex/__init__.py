"""Compatibility re-export layer for the source-layout EUR-Lex package."""

# ruff: noqa: E402,F401,F403,F405

import datetime

import pandas as pd
import rdflib
import requests
from defusedxml import (
    ElementTree as ETree,  # nosec B405 - defusedxml hardens XML parsing
)
from SPARQLWrapper import JSON, SPARQLWrapper

from .celex import *
from .constants import *
from .fetch import *
from .parser import *
from .sparql import *
from .utils import *
