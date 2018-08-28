"""
Test cases targeting streamingphish/configuration.py.
"""
import pytest
from unittest.mock import MagicMock

def test_get_classifier(db, config, monkeypatch):
    def spoofed_clf_in_db():
        return ['classifier_v8']
    monkeypatch.setattr(db, 'available_classifiers', spoofed_clf_in_db)
    config.active_classifier = "classifier_v8"
    assert config._phish_db.verify_classifier_existence.call_count == 1

def test_print_classifier(config, monkeypatch):
    config.print_config()

def test_get_active_classifier(config):
    clf = config.active_classifier
    assert clf
