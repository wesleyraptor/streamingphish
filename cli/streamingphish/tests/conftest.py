"""
Defining fixtures to be shared by all the tests.
"""

import pytest
from unittest.mock import Mock
import pymongo
import mongomock

from streamingphish.configuration import PhishConfig
from streamingphish.features import PhishFeatures
from streamingphish.database import PhishDB
from streamingphish.trainer import PhishTrainer
from streamingphish.predictor import PhishPredictor

@pytest.fixture(scope="session")
def config():
    config = PhishConfig()
    config._phish_db = Mock(spec=PhishDB)
    return config

@pytest.fixture()
def db(monkeypatch):
    # Create a mocked mongodb instance instead of a real one.
    def fake_db():
        return mongomock.MongoClient()

    monkeypatch.setattr('pymongo.MongoClient', fake_db)
    db = PhishDB()
    db._classifiers = Mock()
    return db

@pytest.fixture(scope="session")
def features(config):
    features = PhishFeatures(data_config=config.config['data'])
    features._brands = ['appleid', 'hsbc']
    features._keywords = ['suspended', 'virus', 'update']
    features._fqdn_keywords = ['your', 'sign', 'in', 'com']
    features._similarity_words = ['paypal']
    features._tlds = ['com', 'net', 'org']
    return features

@pytest.fixture(scope="session")
def trainer():
    return PhishTrainer()
