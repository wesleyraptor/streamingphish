"""
Test cases targeting streamingphish/database.py.
"""
import pytest

@pytest.fixture(scope="module")
def artifacts():
    return {'classifier_name': 'classifier_v1', 'key_one': 'value_one'}

### Helper function ###
def spoofed_find_function():
    return [{'_id': 'something', 'classifier_v1': 'blob'}]

def test_save(db, artifacts):
    """Verify transformation of artifacts and save to db."""
    db.save_classifier(artifacts)
    db._classifiers.insert_one.assert_called_with({'classifier_v1': {'key_one': 'value_one'}})

def test_delete(db):
    db.delete_classifier('classifier_v1')
    assert db._classifiers.delete_many.call_count == 1

def test_available_classifiers(db, monkeypatch):
    """Spoofing the return of the find method, verifying classifier name is returned."""
    monkeypatch.setattr(db._classifiers, 'find', spoofed_find_function)
    result = db.available_classifiers() 
    assert result == ['classifier_v1']

@pytest.mark.parametrize("evaluate, result",
[
    ('classifier_v1', True),
    ('nopenopenope', False)
])
def test_verify_classifier(db, monkeypatch, evaluate, result):
    """Spoofing the return of the find method, verifying classifier existence is correct."""
    monkeypatch.setattr(db._classifiers, 'find', spoofed_find_function)
    returned = db.verify_classifier_existence(evaluate)
    assert returned == result

def test_fetch_classifier(db, monkeypatch):
    def spoofed_find_one(name):
        return {'_id': 'who_cares', 'classifier_v5': 'blah'}
    monkeypatch.setattr(db._classifiers, 'find_one', spoofed_find_one)
    result = db.fetch_classifier('classifier_v5')
    assert 'classifier_v5' in result.keys()
