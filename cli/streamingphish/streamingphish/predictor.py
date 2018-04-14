"""
This module is dedicated to taking a trained model and evaluating new FQDNs.
The supported modes are 'certstream' and 'manual'. The 'certstream' mode
evaluates all the FQDNs coming from the Certificate Transparancy log network,
whereas the manual mode simply runs as a CLI utility where one can evaluate
FQDNs in free-form.

See the PhishPredictor class for more info.
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

import logging
import os
from datetime import datetime

import tqdm
import certstream
from termcolor import colored

from .configuration import PhishConfig
from .database import PhishDB

class PhishPredictor:
    """
    Responsible for evaluating new FQDNs either via certstream or manual mode.
    Fetches active classifier from config, loads it from database, and operates
    in the mode requested by the caller.
    """
    def __init__(self):
        """
        Fetch the configuration and database interfaces, configure logging, etc.

        Raises:
            IOError: Active classifier from config not found, user needs to train one.
        """
        self._phish_config = PhishConfig()
        if not self._phish_config.verify_active_classifier_exists():
            raise IOError("[-] Active classifier not found - please train one,"
                          " or update config with name of a trained classifier.")

        # Consider using mongoengine to do this.
        self._logging_enabled = self._phish_config.config['logging']['enabled']
        self._log_tiers = self._phish_config.config['logging_tiers']
        self._log_version = self._phish_config.config['version']
        self._log_path = self._phish_config.config['logging']['path']
        self._colors_enabled = self._phish_config.config['certstream']['colors']
        self._seen_timestamp = self._phish_config.config['certstream']['include_seen_timestamp']
        self._issuer_ca = self._phish_config.config['certstream']['include_issuer_ca_name']
        self._root_ca = self._phish_config.config['certstream']['include_root_ca_name']
        self._certstream_log_source = self._phish_config.config['certstream']['include_log_source']

        # If logging is enabled and log path directory doesn't exist, make it.
        if self._logging_enabled and not os.path.exists(self._log_path):
            os.makedirs(self._log_path)

        # Get active classifier name.
        tqdm.tqdm.write("[*] Fetching active classifier name from config.")
        classifier_name = self._phish_config.active_classifier

        # Fetch classifier artifacts from DB.
        tqdm.tqdm.write("[*] Fetching classifier artifacts from database.")
        self._phish_db = PhishDB()
        artifacts = self._phish_db.fetch_classifier(classifier_name)

        # Decode objects for feature extraction and scoring, assign to self, and then proceed
        # to the correct mode.
        self._features = self._phish_db.restore_python_object(
            artifacts[classifier_name]['feature_extractor'])
        tqdm.tqdm.write("[+] Loaded feature extractor.")
        self._classifier = self._phish_db.restore_python_object(
            artifacts[classifier_name]['classifier'])
        tqdm.tqdm.write("[+] Loaded {} classifier.".format(classifier_name))

    def __call__(self, mode='certstream'):
        """
        Handler for mode of deployment (certstream or manual).

        Args:
            mode (string): Method of deployment ('certstream' or 'manual')

        Raises:
            ValueError: Invalid mode selected (must be certstream or manual).
        """
        # Fetch config, DB, assign config parameters to objects used by this class.
        if mode == 'manual':
            self._manual_mode()
        elif mode == 'certstream':
            # Launch certstream.
            tqdm.tqdm.write("[*] Analysis started - press CTRL+C to quit at anytime.")
            certstream.listen_for_events(self._certstream_mode)
        else:
            raise ValueError("Invalid mode selected - please choose 'manual' or 'certstream'.")

    def _print_result(self, output):
        """
        Takes message, color, level, host, and score, then prints to screen.

        Args:
            output (dictionary): Contains message, color, level, host, and score.
                message (dictionary): Certificate_update dict from certstream.
                color (string): Color to print to screen.
                level (string): Log level i.e. 'high', 'suspicious', 'low'.
                host (string): Predicted FQDN i.e. 'apple1d.spport-account.w5546.tk'
                score (string): Prediction score from classifier.
        """
        # General information items like time, log source, cert authorities, etc.
        general_info = []
        if self._seen_timestamp:
            general_info.append("[{}]".format(
                datetime.fromtimestamp(output['message']['data']['seen']).isoformat()))

        if self._certstream_log_source:
            general_info.append("[{}]".format(output['message']['data']['source']['name']))

        if self._root_ca:
            # Last item in list should be root CA.
            general_info.append("[{}]".format(
                output['message']['data']['chain'][-1]['subject']['O']))

        if self._issuer_ca:
            # First item in list should be issuing CA. Could also get this from
            # the actual leaf certificate.
            general_info.append("[{}]".format(
                output['message']['data']['chain'][0]['subject']['O']))

        if general_info:
            if self._colors_enabled:
                general_output = colored(" ".join(str(item) for item in general_info), 'white',
                                         attrs=["bold",])
            else:
                general_output = " ".join(str(item) for item in general_info)

        # Information specific to the host being evaluated, classifier score, level, etc.
        # We want this to be colored differently from the general info.
        score = "[SCORE:{:.3f}]".format(output['score'])
        scoring_info = []
        scoring_info.extend(("[{}]".format(output['level'].upper()), score, output['host']))

        if self._colors_enabled:
            scoring_output = colored(
                " ".join(str(item) for item in scoring_info), output['color'], attrs=["bold",])
        else:
            scoring_output = " ".join(str(item) for item in scoring_info)
            scoring_output = scoring_output

        if general_info:
            final = "{} {}".format(general_output, scoring_output)
        else:
            final = scoring_output

        tqdm.tqdm.write(final)

        # If enabled, write the flagged domain to its respective log file on disk.
        if self._logging_enabled:
            filename = "{}_v{}.log".format(output['level'], self._log_version)
            file_target = os.path.join(self._log_path, filename)

            with open(file_target, 'a') as outfile:
                outfile.write(output['host'] + "\n")

    def _certstream_mode(self, message, context):
        """
        Deploys loaded classifier against certstream feed.

        Args:
            message (dictionary): SSL certificate and contextual information (cert chain,
                log it came from, etc).
            context (?): I actually don't know, this is from the certstream callback docs.
        """
        if message['message_type'] == "heartbeat":
            return

        if message['message_type'] == "certificate_update":
            # Get all domains, and remove any duplicates of a wildcard domain.
            # A domain being a wildcard could factor into the scoring, but ignore for now.
            hosts = message['data']['leaf_cert']['all_domains']
            for host in hosts:
                if host.startswith('*.') and host[2:] in hosts:
                    hosts.remove(host[2:])

            try:
                scores = self._score(hosts)
            except Exception as error:
                # Write to system.log, assign prediction score of 0, continue.
                logging.error("{}: {}".format(error, message))
                scores = ([0] * len(hosts))

            # For each host, evaluate score, print to stdout, log, etc.
            for host, score in zip(hosts, scores):

                # Evaluate score from host against each threshold in the config.
                for tier in sorted(self._log_tiers, key=lambda x:
                                   self._log_tiers[x]['threshold'], reverse=True):

                    # If score is above threshold, print to screen, log if enabled,
                    # and break out of this loop to evaluate the next host.
                    if score > self._log_tiers[tier]['threshold']:
                        result = {}
                        result['message'] = message
                        result['color'] = self._log_tiers[tier]['color']
                        result['level'] = tier
                        result['host'] = host
                        result['score'] = score
                        self._print_result(result)

                        # Break, we don't need to iterate through any more thresholds.
                        break

    def _manual_mode(self):
        """
        Deploys loaded classifier in manual mode. User can type 'exit' or 'quit' at any time.

        No args and doesn't return anything, simply returns to caller when user exits.
        """
        tqdm.tqdm.write("[+] Deploying in manual mode. Type 'exit' or 'quit' at"
                        " any time to return to the main menu.")
        while True:
            evaluate = str(input("FQDN/Host/URL: ").lower())
            if evaluate not in ['quit', 'exit']:
                result = self._score([evaluate])
                if result[0] >= 0.5:
                    prediction = "PHISHING"
                else:
                    prediction = "NOT PHISHING"
                tqdm.tqdm.write("[{}]: {:.3f}".format(prediction, result[0]))
            else:
                # User wants to quit - abandon ship.
                tqdm.tqdm.write("[+] Returning to main menu.")
                break

    def _score(self, samples):
        """
        Takes a list of FQDNs, computes features, transforms to feature vector from training,
        and predicts them as phishing or not phishing (< or > 0.5).

        Args:
            samples (list): FQDN/Hosts to evaluate.

        Return:
            result (list): Scores from classifier i.e. [1.000, 0.981, 0.001].
        """
        sample_features = self._features.compute_features(samples, values_only=False)
        scores = self._classifier.predict_proba(sample_features['values'])[:, 1]

        result = []
        for score in scores:
            result.append(score)
        return result
