"""Delt pytest-oppsett: en DB-sesjon per test, alltid rullet tilbake etterpå.

join_transaction_mode="create_savepoint" gjør at kode under test kan kalle
session.commit() som normalt (den committer bare til en SAVEPOINT), mens hele
testens ytre transaksjon rulles tilbake i teardown - databasen står tom igjen
til neste test, uavhengig av hvilken lokal Postgres denne kjøres mot.
"""

import pytest
from sqlalchemy.orm import Session

from app.db import engine


@pytest.fixture()
def db() -> Session:
    connection = engine.connect()
    outer_transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        outer_transaction.rollback()
        connection.close()
