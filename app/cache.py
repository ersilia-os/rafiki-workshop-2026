"""Cached data loaders, shared by every step.

Each cache key includes the file's mtime, so regenerating a descriptor or a
projection is picked up instead of being served stale from a previous run.
"""

import os

import streamlit as st

from utils import (
    data_path, load_analogues, load_descriptors, load_library, load_projection,
    load_rafiki_ids, load_training_data,
)


def data_version(filename):
    return os.path.getmtime(data_path(filename))


@st.cache_data(show_spinner=False)
def _training_data(filename, version):
    return load_training_data(filename)


@st.cache_data(show_spinner=False)
def _descriptors(filename, version):
    return load_descriptors(filename)


@st.cache_data(show_spinner=False)
def _library(filename, version):
    return load_library(filename)


@st.cache_data(show_spinner=False)
def _projection(filename, version):
    return load_projection(filename)


@st.cache_data(show_spinner=False)
def _rafiki_ids(filename, version):
    return load_rafiki_ids(filename)


@st.cache_data(show_spinner=False)
def _analogues(filename, version):
    return load_analogues(filename)


def cached_training_data(filename):
    return _training_data(filename, data_version(filename))


def cached_descriptors(filename):
    return _descriptors(filename, data_version(filename))


def cached_library(filename):
    return _library(filename, data_version(filename))


def cached_projection(filename):
    return _projection(filename, data_version(filename))


def cached_rafiki_ids(filename):
    return _rafiki_ids(filename, data_version(filename))


def cached_analogues(filename):
    return _analogues(filename, data_version(filename))
