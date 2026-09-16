import os
# Remove the test database file if it exists
test_db = "./test.db"
if os.path.exists(test_db):
    os.remove(test_db)

os.environ["POSTGRES_DATABASE_URL"] = f"sqlite:///{test_db}"
os.environ["TESTING"] = "1"

# Now import the app and the db
from hermes.__init__ import app
from hermes.crm import engine, SessionLocal, Base

import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()