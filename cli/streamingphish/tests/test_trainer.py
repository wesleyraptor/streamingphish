"""
Test cases targeting streamingphish/trainer.py.
"""
import pytest
from unittest.mock import MagicMock
from collections import OrderedDict

def test_model_generation(trainer, monkeypatch):
    def sample_training():
        result = {}
        for x in range(0, 20):
            result['appleid-apple.susp.{}.tk'.format(x)] =  1
            result['www.{}.google.com'.format(x)] = 0
        return result

    monkeypatch.setattr(trainer, '_load_training_data', sample_training)
    result = trainer.generate_model()

    # Check that the classifier, metrics, and feature extractor were returned from training.
    assert all(x in ['metrics', 'classifier', 'feature_extractor'] for x in result.keys())

def test_load_training_data(trainer):
    data = trainer._load_training_data()
    assert isinstance(data, OrderedDict)
