"""
Defining fixtures to be shared by all the tests.
"""

import pytest
from unittest.mock import MagicMock
from _pytest.monkeypatch import MonkeyPatch
import pymongo
import pickle

from streamingphish.configuration import PhishConfig
from streamingphish.features import PhishFeatures
from streamingphish.database import PhishDB
from streamingphish.trainer import PhishTrainer
from streamingphish import cli
from streamingphish import predictor

@pytest.fixture(scope="session")
def monkeypatch_session():
    # Workaround for patching session-scoped fixtures.
    # https://github.com/pytest-dev/pytest/issues/1872
    m = MonkeyPatch()
    yield m
    m.undo()

@pytest.fixture(scope="session")
def db(monkeypatch_session):
    monkeypatch_session.setattr(pymongo, 'MongoClient', MagicMock())
    db = PhishDB()
    return db

@pytest.fixture(scope="session")
def config(db):
    config = PhishConfig()
    config._phish_db = MagicMock()
    return config

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

@pytest.fixture(scope="session")
def phish_predictor(features, config, monkeypatch_session):
    def sample_config():
        return config
    def sample_data(data, encoding):
        return 'blah'

    monkeypatch_session.setattr(pickle, 'loads', sample_data)
    monkeypatch_session.setattr(predictor, 'PhishConfig', sample_config)
    phish_predictor = predictor.PhishPredictor()
    return phish_predictor

@pytest.fixture(scope='session')
def phish_cli(config, db, monkeypatch_session):
    def sample_config():
        return config
    def sample_db():
        return db
    def sample_input(dummy):
        return '6'

    monkeypatch_session.setattr(cli, 'PhishDB', sample_db)
    monkeypatch_session.setattr(cli, 'PhishConfig', sample_config)
    cli.input = sample_input
    with pytest.raises(SystemExit):
        return cli.PhishCLI()
