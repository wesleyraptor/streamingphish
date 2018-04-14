"""
Test cases targeting streamingphish/features.py
"""
import re
from collections import defaultdict

import pytest

@pytest.fixture(scope="module")
def sample(features):
    fqdn = "www.appleid.com-suspicious.1234.com"
    sample = features._fqdn_parts(fqdn=fqdn)
    sample['fqdn'] = features._remove_common_hosts(fqdn=fqdn)
    sample['fqdn_words'] = re.split('\W+', fqdn)
    return sample

def test_fqdn_parts(features):
    result = features._fqdn_parts(fqdn='www.google.com')
    assert result['subdomain'] == 'www'
    assert result['domain'] == 'google'
    assert result['tld'] == 'com'

@pytest.mark.parametrize("raw, filtered",
[
    ('mail.google.com', 'google.com'),
    ('*.google.com', 'google.com'),
    ('www.google.com', 'google.com'),
    ('cpanel.google.com', 'google.com'),
    ('webmail.google.com', 'google.com'),
    ('webdisk.google.com', 'google.com'),
    ('autodiscover.google.com', 'google.com'),
    ('wvw.google.com', 'wvw.google.com')
])
def test_remove_common_hosts(features, raw, filtered):
    assert features._remove_common_hosts(raw) == filtered

@pytest.mark.parametrize("domain, feature, expected",
[
    ({'tld': 'com'}, 'tld_com', 1),
    ({'tld': 'net'}, 'tld_net', 1),
    ({'tld': 'com'}, 'tld_org', 0),
])
def test_extract_tld(features, domain, feature, expected):
    result = features._fe_extract_tld(sample=domain)
    assert result[feature] == expected

def test_brand_presence(features, sample):
    result = features._fe_brand_presence(sample=sample)
    assert result['appleid_brand_subdomain'] == 1

def test_keyword_match(features, sample):
    result = features._fe_keyword_match(sample=sample)
    assert result['update_kw'] == 0

def test_keyword_match_fqdn_words(features, sample):
    result = features._fe_keyword_match_fqdn_words(sample=sample)
    assert result['com_kw_fqdn_words'] == 1

def test_domain_entropy(features, sample):
    result = features._fe_compute_domain_entropy(sample=sample)
    assert result['entropy'] == 2.0

@pytest.mark.parametrize('evaluate, expected',
[
    ({'fqdn_words': ['www', 'paypal', 'notmalware']}, 0),
    ({'fqdn_words': ['www', 'payyyypal', 'notmalware']}, 0),
    ({'fqdn_words': ['com', 'pavpal', 'signin']}, 1)
])
def test_phishing_word_similarity(features, evaluate, expected):
    result = features._fe_check_phishing_similarity_words(sample=evaluate)
    assert result['paypal_lev_1'] == expected

def test_num_dashes(features, sample):
    result = features._fe_number_of_dashes(sample=sample)
    assert result['num_dashes'] == 1

def test_num_periods(features, sample):
    result = features._fe_number_of_periods(sample=sample)
    assert result['num_periods'] == 3

@pytest.mark.parametrize("fqdns, flag, expected",
[
    (['www.espn.com', 'com-apple.id.iforgot.blah.org'], True, ['values']),
    (['google.com', 'reddit.com'], False, ['values', 'names'])
])
def test_compute_values_only(features, fqdns, flag, expected):
    fqdns = ['www.espn.com', 'com-apple.id.iforgot.whooodat.io']
    result = features.compute_features(fqdns=fqdns, values_only=flag)
    assert all([x in result.keys() for x in expected])


