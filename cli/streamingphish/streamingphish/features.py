"""
This module is responsible solely for extracting features from data being
evaluated. The functions that extract features start with _fe_, and are
dynamically called by the compute_features() function in the PhishFeatures
class.

See the PhishFeatures class for more details.
"""
__copyright__ = """
   Copyright 2018 Wes Connell

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
__license__ = "Apache 2.0"

import os
import math
import re
from collections import Counter, OrderedDict

from Levenshtein import distance
import tldextract
import numpy as np

class PhishFeatures:
    """
    Library of functions that extract features from FQDNs. Each of those functions returns
    a dictionary with feature names and their corresponding values, i.e.:
        {
            'num_dashes': 0,
            'paypal_kw_present': 1,
            'alexa_25k_domain': 0,
            'entropy': 0
        }
    """

    def __init__(self, data_config):
        """
        Loads keywords, phishing words, and targeted brands used by other functions in this class.

        Args:
            data_config (dictionary): Contains paths to files on disk needed for training.
        """
        self._brands = self._load_from_directory(data_config['targeted_brands_dir'])
        self._keywords = self._load_from_directory(data_config['keywords_dir'])
        self._fqdn_keywords = self._load_from_directory(data_config['fqdn_keywords_dir'])
        self._similarity_words = self._load_from_directory(data_config['similarity_words_dir'])
        self._tlds = self._load_from_directory(data_config['tld_dir'])

    @staticmethod
    def _remove_common_hosts(fqdn):
        """
        Takes a FQDN, removes common hosts prepended to it in the subdomain, and returns it.

        Args:
            fqdn (string): FQDN from certstream.

        Returns:
            fqdn (string): FQDN with common benign hosts removed (these hosts have no bearing
                on malicious/benign determination).
        """
        fqdn_parts = fqdn.split(".", 1)
        common_hosts = ["*", "www", "mail", "cpanel", "webmail",
                        "webdisk", "autodiscover"]

        if len(fqdn_parts) > 1:
            if fqdn_parts[0] in common_hosts:
                return fqdn_parts[1]

        return fqdn

    @staticmethod
    def _fqdn_parts(fqdn):
        """
        Break apart domain parts and return a dictionary representing the individual attributes
        like subdomain, domain, and tld.

        Args:
            fqdn (string): FQDN being analyzed.

        Returns:
            result (dictionary): Each part of the fqdn, i.e. subdomain, domain, domain + tld
        """
        parts = tldextract.extract(fqdn)
        result = {}
        result['subdomain'] = parts.subdomain
        result['domain'] = parts.domain
        result['tld'] = parts.suffix

        return result

    @staticmethod
    def _load_from_directory(path):
        """
        Read all text files from a directory on disk, creates list, and returns.

        Args:
            path (string): Path to directory on disk, i.e. '/opt/streamingphish/keywords/'

        Returns:
            values (list): Values from all text files in the supplied directory.
        """
        values = []

        # Load brand names from all the text files in the provided folder.
        for root, _, files in os.walk(path):
            files = [f for f in files if not f[0] == "."]
            for f in files:
                with open(os.path.join(root, f)) as infile:
                    for item in infile.readlines():
                        values.append(item.strip('\n'))

        return values

    def compute_features(self, fqdns, values_only=True):
        """
        Calls all the methods in this class that begin with '_fe_'. Not sure how pythonic
        this is, but I wanted dynamic functions so those can be written without having
        to manually define them here. Shooting for how python's unittest module works,
        there's a chance this is a python crime.

        Args:
            fqdns (list): fqdns to compute features for.
            values_only (boolean, optional): Instead computes a np array w/ values only
                and returns that instead of a list of dictionaries (reduces perf overhead).

        Returns:
            result (dict): 'values' will always be returned - list of feature values of
                each FQDN being analyzed. Optional key included is 'names', which is the
                feature vector and will be returned if values_only=True.
        """
        result = {}

        # Raw features are a list of dictionaries, where keys = feature names and
        # values = feature values.
        features = []
        for fqdn in fqdns:
            sample = self._fqdn_parts(fqdn=fqdn)
            sample['fqdn'] = self._remove_common_hosts(fqdn=fqdn)
            sample['fqdn_words'] = re.split('\W+', fqdn)

            analysis = OrderedDict()
            for item in dir(self):
                if item.startswith('_fe_'):
                    method = getattr(self, item)
                    result = method(sample)
                    analysis = {**analysis, **result}
            # Must sort dictionary by key before adding.
            analysis = OrderedDict(sorted(analysis.items()))
            features.append(analysis)

        # Split out keys and values from list of dictionaries. Keys = feature names, and
        # values = feature values.
        result = {}
        result['values'] = []
        for item in features:
            result['values'].append(np.fromiter(item.values(), dtype=float))

        if not values_only:
            # Take the dictionary keys from the first item - this is the feature vector.
            result['names'] = features[0].keys()

        return result

    def _fe_extract_tld(self, sample):
        """
        Check if TLD is in a list of ~30 TLDs indicative of phishing / not phishing. Originally,
        this was a categorical feature extended via get_dummies / one hot encoding, but it was
        adding too many unnecessary features to the feature vector resulting in a large tax
        performance wise.

        Args:
            sample (dictionary): Info about the sample being analyzed i.e. subdomain, tld, fqdn

        Returns:
            result (dictionary): Keys are feature names, values are feature scores.
        """
        result = OrderedDict()
        for item in self._tlds:
            result["tld_{}".format(item)] = 1 if item == sample['tld'] else 0

        return result

    def _fe_brand_presence(self, sample):
        """
        Checks for brands targeted by phishing in subdomain (likely phishing) and in domain
        + TLD (not phishing).

        Args:
            sample (dictionary): Info about the sample being analyzed i.e. subdomain, tld, fqdn

        Retuns:
            result (dictionary): Keys are feature names, values are feature scores.
        """
        result = OrderedDict()
        for item in self._brands:
            result["{}_brand_subdomain".format(item)] = 1 if item in sample['subdomain'] else 0
            result["{}_brand_domain".format(item)] = 1 if item in sample['domain'] else 0

        return result

    def _fe_keyword_match(self, sample):
        """
        Look for presence of keywords anywhere in the FQDN i.e. 'account' would match on
        'dswaccounting.tk'.

        Args:
            sample (dictionary): Info about the sample being analyzed i.e. subdomain, tld, fqdn

        Returns:
            result (dictionary): Keys are feature names, values are feature scores.
        """
        result = OrderedDict()

        for item in self._keywords:
            result[item + "_kw"] = 1 if item in sample['fqdn'] else 0

        return result

    def _fe_keyword_match_fqdn_words(self, sample):
        """
        Compare FQDN words (previous regex on special characters) against a list of common
        phishing keywords, look for exact match on those words. Probably more decisive
        in identifying phishing domains.

        Args:
            sample (dictionary): Info about the sample being analyzed i.e. subdomain, tld, fqdn

        Returns:
            result (dictionary): Keys are feature names, values are feature scores.
        """
        result = OrderedDict()

        for item in self._fqdn_keywords:
            result[item + "_kw_fqdn_words"] = 1 if item in sample['fqdn_words'] else 0

        return result

    @staticmethod
    def _fe_compute_domain_entropy(sample):
        """
        Takes domain name from FQDN and computes entropy (randomness, repeated characters, etc).

        Args:
            sample (dictionary): Info about the sample being analyzed i.e. subdomain, tld, fqdn

        Returns:
            result (dictionary): Keys are feature names, values are feature scores.
        """
        # Compute entropy of domain.
        result = OrderedDict()
        p, lns = Counter(sample['domain']), float(len(sample['domain']))
        entropy = -sum(count / lns * math.log(count / lns, 2) for count in list(p.values()))

        result['entropy'] = entropy
        return result

    def _fe_check_phishing_similarity_words(self, sample):
        """
        Takes a list of words from the FQDN (split by special characters) and checks them
        for similarity against words commonly disguised as phishing words. This method only
        searches for a distance of 1.
            i.e. 'pavpal' = 1 for 'paypal', 'verifycation' = 1 for 'verification',
                'app1eid' = 1 for 'appleid'.

        Args:
            sample (dictionary): Info about the sample being analyzed i.e. subdomain, tld, fqdn

        Returns:
            result (dictionary): Keys are feature names, values are feature scores.
        """
        result = OrderedDict()

        for key in self._similarity_words:
            result[key + "_lev_1"] = 0

            for word in sample['fqdn_words']:
                if distance(word, key) == 1:
                    result[key + "_lev_1"] = 1

        return result

    @staticmethod
    def _fe_number_of_dashes(sample):
        """
        Compute the number of dashes - several could be a sign of URL padding, etc.

        Args:
            sample (dictionary): Info about the sample being analyzed i.e. subdomain, tld, fqdn

        Returns:
            result (dictionary): Keys are feature names, values are feature scores.
        """
        result = OrderedDict()
        result['num_dashes'] = 0 if "xn--" in sample['fqdn'] else sample['fqdn'].count("-")
        return result

    @staticmethod
    def _fe_number_of_periods(sample):
        """
        Compute number of periods - several subdomains could be indicative of a phishing domain.

        Args:
            sample (dictionary): Info about the sample being analyzed i.e. subdomain, tld, fqdn

        Returns:
            result (dictionary): Keys are feature names, values are feature scores.
        """
        result = OrderedDict()
        result['num_periods'] = sample['fqdn'].count(".")
        return result
