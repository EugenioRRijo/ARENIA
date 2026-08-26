"""Fixtures compartidas de la suite.

Los datos viven en tests/fixtures/apu_linea_base.py (única copia, principio DRY).
"""

import pytest

from tests.fixtures import apu_linea_base as linea_base


@pytest.fixture(scope="session")
def parametros_linea_base():
    return linea_base.PARAMETROS_LINEA_BASE


@pytest.fixture(scope="session")
def apus_linea_base():
    return linea_base.APUS_LINEA_BASE


@pytest.fixture(scope="session")
def presupuesto_auditado():
    return linea_base.PRESUPUESTO_AUDITADO


@pytest.fixture(scope="session")
def curva_auditada():
    return linea_base.CURVA_AUDITADA
