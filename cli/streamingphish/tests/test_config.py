"""
Test cases targeting streamingphish/configuration.py.
"""
import pytest

def test_get_classifier(config, monkeypatch):
    config.active_classifier = "new_clf"
    assert config._phish_db.verify_classifier_existence.call_count == 1
