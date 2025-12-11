"""
Performance benchmarks for conda-pypi using pytest-codspeed.

These benchmarks measure the performance of key operations in conda-pypi,
including package conversion, dependency resolution, and installation.
"""

from __future__ import annotations

import os
from pathlib import Path

from conda.models.match_spec import MatchSpec
from conda.testing.fixtures import TmpEnvFixture
from pytest_codspeed import BenchmarkFixture
from pytest_mock import MockerFixture

from conda_pypi.convert_tree import ConvertTree
from conda_pypi.downloader import get_package_finder

import pytest

REPO = Path(__file__).parents[1] / "synthetic_repo"


def test_benchmark_convert_single_package(
    benchmark: BenchmarkFixture,
    tmp_env: TmpEnvFixture,
    tmp_path: Path,
    monkeypatch: MockerFixture,
):
    """
    Benchmark converting a single PyPI package to conda format.
    """
    CONDA_PKGS_DIRS = tmp_path / "conda-pkgs"
    CONDA_PKGS_DIRS.mkdir()

    WHEEL_DIR = tmp_path / "wheels"
    WHEEL_DIR.mkdir(exist_ok=True)

    REPO.mkdir(parents=True, exist_ok=True)

    TARGET_DEP = MatchSpec("certifi")  # type: ignore

    # Defeat package cache for ConvertTree
    monkeypatch.setitem(os.environ, "CONDA_PKGS_DIRS", str(CONDA_PKGS_DIRS))

    with tmp_env("python=3.12", "pip") as prefix:
        converter = ConvertTree(prefix, repo=REPO, override_channels=True)

        @benchmark
        def run():
            converter.convert_tree([TARGET_DEP])


def test_benchmark_convert_package_with_dependencies(
    benchmark: BenchmarkFixture,
    tmp_env: TmpEnvFixture,
    tmp_path: Path,
    monkeypatch: MockerFixture,
):
    """
    Benchmark converting a PyPI package with dependencies to conda format.
    """
    CONDA_PKGS_DIRS = tmp_path / "conda-pkgs"
    CONDA_PKGS_DIRS.mkdir()

    WHEEL_DIR = tmp_path / "wheels"
    WHEEL_DIR.mkdir(exist_ok=True)

    REPO.mkdir(parents=True, exist_ok=True)

    # twine has multiple dependencies, making it a good benchmark target
    TARGET_DEP = MatchSpec("twine==5.1.1")  # type: ignore

    # Defeat package cache for ConvertTree
    monkeypatch.setitem(os.environ, "CONDA_PKGS_DIRS", str(CONDA_PKGS_DIRS))

    with tmp_env("python=3.12", "pip") as prefix:
        converter = ConvertTree(prefix, repo=REPO, override_channels=True)

        @benchmark
        def run():
            converter.convert_tree([TARGET_DEP])


@pytest.mark.parametrize("package_spec", ["certifi", "tomli==2.0.1", "requests"])
def test_benchmark_package_finder(
    benchmark: BenchmarkFixture,
    tmp_env: TmpEnvFixture,
    package_spec: str,
):
    """
    Benchmark package finder performance for different package specifications.
    """
    with tmp_env("python=3.12", "pip") as prefix:
        finder = get_package_finder(prefix)

        @benchmark
        def run():
            # Find the package
            result = finder.find_best_match(package_spec.split("==")[0])
            return result


def test_benchmark_convert_local_package(
    benchmark: BenchmarkFixture,
    tmp_env: TmpEnvFixture,
    tmp_path: Path,
    monkeypatch: MockerFixture,
    pypi_local_index: str,
):
    """
    Benchmark converting a local PyPI package to conda format.
    """
    CONDA_PKGS_DIRS = tmp_path / "conda-pkgs"
    CONDA_PKGS_DIRS.mkdir()

    WHEEL_DIR = tmp_path / "wheels"
    WHEEL_DIR.mkdir(exist_ok=True)

    REPO.mkdir(parents=True, exist_ok=True)

    TARGET_DEP = MatchSpec("demo-package")  # type: ignore

    # Defeat package cache for ConvertTree
    monkeypatch.setitem(os.environ, "CONDA_PKGS_DIRS", str(CONDA_PKGS_DIRS))

    with tmp_env("python=3.12", "pip") as prefix:
        finder = get_package_finder(prefix, (pypi_local_index,))
        converter = ConvertTree(prefix, repo=REPO, override_channels=True, finder=finder)

        @benchmark
        def run():
            converter.convert_tree([TARGET_DEP])
