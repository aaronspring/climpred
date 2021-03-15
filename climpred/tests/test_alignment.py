"""Identical to test_alignment_old.py but new implementation for HindcastEnsemble.verify()."""

import logging

import numpy as np
import pytest
import xskillscore as xs

from climpred import HindcastEnsemble
from climpred.exceptions import CoordinateError
from climpred.prediction import compute_hindcast

verify_kw = dict(metric="mse", comparison="e2o", dim="init")


def test_same_inits_initializations(hindcast_obs_1d_for_alignment, caplog):
    """Tests that inits are identical at all leads for `same_inits` alignment."""
    with caplog.at_level(logging.INFO):
        hindcast_obs_1d_for_alignment.verify(alignment="same_inits", **verify_kw)
        for i, record in enumerate(caplog.record_tuples):
            if i >= 2:
                print(record)
                assert "inits: 1954-01-01 00:00:00-2007-01-01 00:00:00" in record[2]


def test_same_inits_verification_dates(hindcast_obs_1d_for_alignment, caplog):
    """Tests that appropriate verifs are being used at each lead for `same_inits`
    alignment."""
    with caplog.at_level(logging.INFO):
        FIRST_INIT, LAST_INIT = 1954, 2007
        hindcast_obs_1d_for_alignment.verify(
            alignment="same_inits",
            **verify_kw,
        )
        print(caplog.record_tuples)
        nleads = hindcast_obs_1d_for_alignment.get_initialized()["lead"].size
        for i, record in zip(
            np.arange(nleads + 2),
            caplog.record_tuples,
        ):
            if i >= 2:
                print(record)
                assert (
                    f"verifs: {FIRST_INIT+i+1}-01-01 00:00:00-{LAST_INIT+i+1}-01-01"
                    in record[2]
                )


@pytest.mark.parametrize("alignment", ["same_inits", "same_verifs"])
def test_disjoint_verif_time(small_initialized_da, small_verif_da, alignment):
    """Tests that alignment works with disjoint time in the verification
    data, i.e., non-continuous time sampling to verify against."""
    hind = small_initialized_da.to_dataset(name="SST")
    verif = small_verif_da.drop_sel(time=1992).to_dataset(name="SST")
    hindcast = HindcastEnsemble(hind).add_observations(verif)
    actual = hindcast.verify(alignment=alignment, **verify_kw)
    assert actual.SST.notnull().all()
    # hindcast inits: [1990, 1991, 1992, 1993]
    # verif times: [1990, 1991, 1993, 1994]
    a = hind.sel(init=[1990, 1992, 1993]).rename({"init": "time"})
    b = verif.sel(time=[1991, 1993, 1994])
    a["time"] = b["time"]
    expected = xs.mse(a, b, "time")
    assert actual == expected


@pytest.mark.parametrize("alignment", ["same_inits", "same_verifs"])
def test_disjoint_inits(small_initialized_da, small_verif_da, alignment):
    """Tests that alignment works with disjoint inits in the verification
    data, i.e., non-continuous initializing to verify with."""
    hind = small_initialized_da.drop_sel(init=1991).to_dataset(name="SST")
    verif = small_verif_da.to_dataset(name="SST")
    hindcast = HindcastEnsemble(hind).add_observations(verif)
    actual = hindcast.verify(alignment=alignment, **verify_kw)
    assert actual.SST.notnull().all()
    # hindcast inits: [1990, 1992, 1993]
    # verif times: [1990, 1991, 1992, 1993, 1994]
    a = hind.rename({"init": "time"})
    b = verif.sel(time=[1991, 1993, 1994])
    a["time"] = b["time"]
    expected = xs.mse(a, b, "time")
    assert actual == expected


def test_same_verifs_verification_dates(hindcast_obs_1d_for_alignment, caplog):
    """Tests that verifs are identical at all leads for `same_verifs` alignment."""
    with caplog.at_level(logging.INFO):
        hindcast_obs_1d_for_alignment.verify(alignment="same_verifs", **verify_kw)
        for i, record in enumerate(caplog.record_tuples):
            if i >= 2:
                print(record)
                assert "verifs: 1964-01-01 00:00:00-2017-01-01 00:00:00" in record[2]


def test_same_verifs_initializations(hindcast_obs_1d_for_alignment, caplog):
    """Tests that appropriate verifs are being used at each lead for `same_inits`
    alignment."""
    with caplog.at_level(logging.INFO):
        FIRST_INIT, LAST_INIT = 1964, 2017
        hindcast_obs_1d_for_alignment.verify(alignment="same_verifs", **verify_kw)
        nleads = hindcast_obs_1d_for_alignment.get_initialized()["lead"].size
        for i, record in zip(
            np.arange(nleads + 2),
            caplog.record_tuples,
        ):
            if i >= 2:
                print(record)
                assert (
                    f"inits: {FIRST_INIT-i-1}-01-01 00:00:00-{LAST_INIT-i-1}-01-01 00:00:00"
                    in record[2]
                )


def test_same_verifs_raises_error_when_not_possible(hindcast_obs_1d_for_alignment):
    """Tests that appropriate error is raised when a common set of verification dates
    cannot be found with the supplied initializations."""
    hind = hindcast_obs_1d_for_alignment.isel(lead=slice(0, 3), init=[1, 3, 5, 7, 9])
    with pytest.raises(CoordinateError):
        hind.verify(alignment="same_verifs", **verify_kw)


def test_maximize_alignment_inits(hindcast_obs_1d_for_alignment, caplog):
    """Tests that appropriate inits are selected for `maximize` alignment."""
    with caplog.at_level(logging.INFO):
        hindcast_obs_1d_for_alignment.verify(alignment="maximize", **verify_kw)
        # Add dummy values for the first two lines since they are just metadata.
        for i, record in zip(
            np.concatenate(
                ([0, 0], hindcast_obs_1d_for_alignment.get_initialized().lead.values)
            ),
            caplog.record_tuples,
        ):
            if i >= 1:
                print(record)
                assert (
                    f"inits: 1954-01-01 00:00:00-{2016-i-1}-01-01 00:00:00" in record[2]
                )


def test_maximize_alignment_verifs(hindcast_obs_1d_for_alignment, caplog):
    """Tests that appropriate verifs are selected for `maximize` alignment."""
    with caplog.at_level(logging.INFO):
        hindcast_obs_1d_for_alignment.verify(alignment="maximize", **verify_kw)
        # Add dummy values for the first two lines since they are just metadata.
        for i, record in zip(
            np.concatenate(
                ([0, 0], hindcast_obs_1d_for_alignment.get_initialized().lead.values)
            ),
            caplog.record_tuples,
        ):
            if i >= 1:
                print(record)
                assert (
                    f"verifs: {1955+i+1}-01-01 00:00:00-2017-01-01 00:00:00"
                    in record[2]
                )
