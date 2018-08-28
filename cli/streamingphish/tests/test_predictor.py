import tqdm
import json
import pytest
from unittest.mock import MagicMock

from streamingphish import predictor

@pytest.fixture(scope="module")
def sample_result():
    with open('tests/data/sample_result.json') as infile:
        sample = json.loads(infile.read())
    return sample

@pytest.fixture(scope="module")
def sample_message():
    with open('tests/data/sample_message.json') as infile:
        sample = json.loads(infile.read())
    return sample

def test_manual_mode_exit(phish_predictor, monkeypatch):
    def sample_input(dummy):
        return 'exit'

    predictor.input = sample_input
    monkeypatch.setattr(tqdm.tqdm, 'write', MagicMock())
    phish_predictor._manual_mode()
    tqdm.tqdm.write.assert_any_call("[+] Returning to main menu.")

def test_print_result(phish_predictor, sample_result, monkeypatch):
    monkeypatch.setattr(tqdm.tqdm, 'write', MagicMock())
    phish_predictor._print_result(sample_result)
    assert tqdm.tqdm.write.called

def test_certstream_ingest(phish_predictor, sample_message, monkeypatch):
    monkeypatch.setattr(predictor.PhishPredictor, '_score', MagicMock())
    phish_predictor._certstream_mode(sample_message, context=None)
    assert predictor.PhishPredictor._score.call_count == 1
