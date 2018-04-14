"""
Interface for the configuration, which is a YAML file. The configuration enables users
to toggle logging settings, thresholds, paths to data files, etc.

See the PhishConfig object for more details.
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

import yaml
import tqdm

from .database import PhishDB

CONFIG_PATH = "/opt/streamingphish/config/config.yaml"

class PhishConfig:
    """
    Represents the configuration, which stores directory paths and logging information for
    the command line tool. Presently, this information is persisted to disk in a YAML file
    named config.yaml.
    """

    def __init__(self):
        self.config = self._read_yaml_config()
        self._phish_db = PhishDB()

    @staticmethod
    def _read_yaml_config():
        """
        Reads yaml config from disk to create config object.

        Returns:
            config (dictionary): Configuration for scoring, classifiers, logging, etc.
        """
        with open(CONFIG_PATH) as yamlfile:
            config = yaml.load(yamlfile)
        return config

    def _save_config(self):
        """
        Saves yaml config file to disk.

        No parameters and doesn't return anything.
        """
        with open(CONFIG_PATH, "w") as outfile:
            yaml.dump(self.config, outfile, default_flow_style=False)

    def print_config(self):
        """
        Prints config to the screen.

        No parameters and doesn't return anything.
        """
        tqdm.tqdm.write("[*] Printing configuration...")
        tqdm.tqdm.write(yaml.dump(self.config, default_flow_style=False))

    @property
    def active_classifier(self):
        """
        Return current value for active classifier in the config.

        Returns:
            classifier (string): Name of classifier currently active.
        """
        return self.config['classifier']['active']

    @active_classifier.setter
    def active_classifier(self, new_classifier):
        """
        Sets classifier name to config object and saves to the yaml file on disk.

        Args:
            new_classifier (string): Name of classifier to active.

        Raises:
            ValueError: If classifier is active in config but missing from database.
        """
        if not self._phish_db.verify_classifier_existence(new_classifier):
            raise ValueError('Classifier not found in database.')

        self.config['classifier']['active'] = new_classifier
        self._save_config()
        tqdm.tqdm.write("[+] Activated new classifier, {}, in "
                        "configuration.".format(new_classifier))

    def verify_active_classifier_exists(self):
        """
        Ensure the active classifier in the config is present in the database.
        Users will have to train their own classifier before using in manual mode
            or deploying against certstream.

        Returns:
            True if classifier exists, False if not.
        """
        if self._phish_db.verify_classifier_existence(self.active_classifier):
            return True
        return False
