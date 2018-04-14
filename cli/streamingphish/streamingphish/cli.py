#!/usr/bin/python3
"""
The CLI tool is driven by this module - simply create an instance of PhishCLI().

Need to add log level setting from the config.

See the PhishCLI class object for more details.
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
import sys
import json
import logging

import tqdm

from .database import PhishDB
from .configuration import PhishConfig
from .trainer import PhishTrainer
from .predictor import PhishPredictor

# :)
VALID_ANSWERS = ['y', 'yes', 'yea', 'sure', 'alright', 'fine', 'n', 'no', 'nope', 'nawww']
YES_ANSWERS = ['y', 'yes', 'yea', 'sure', 'alright', 'fine']

MAIN_MENU = """
1. Deploy phishing classifier against certstream feed.
2. Operate phishing classifier in manual mode.
3. Manage classifiers (list active classifier and show available classifiers).
4. Train a new classifier.
5. Print configuration.
6. Exit.\n"""

CLASSIFIERS_MENU = """
1. Summarize accuracy metrics across all trained classifiers.
2. Show performance metrics from a single classifier.
3. Change the active classifier.
4. Delete a classifier.
5. Return to the main menu.\n"""

BANNER = r"""
   _____ __                            _            
  / ___// /_________  ____ _____ ___  (_)___  ____ _
  \__ \/ __/ ___/ _ \/ __ `/ __ `__ \/ / __ \/ __ `/
 ___/ / /_/ /  /  __/ /_/ / / / / / / / / / / /_/ / 
/____/\__/_/   \___/\__,_/_/ /_/ /_/_/_/ /_/\__, /  
    ____  __    _      __                  /____/   
   / __ \/ /_  (_)____/ /_                          
  / /_/ / __ \/ / ___/ __ \                         
 / ____/ / / / (__  ) / / /                         
/_/   /_/ /_/_/____/_/ /_/         by Wes Connell                 
                                      @wesleyraptor              
"""

class PhishCLI:
    """
    Represents command-line interface for using streamingphish and using
    all of its capabilities, i.e. training classifiers, scoring domains in
    manual mode, scoring against certstream, etc.
    """

    def __init__(self):
        self._phish_db = PhishDB()
        self._phish_config = PhishConfig()
        self._configure_logging()
        self._run()

    def _configure_logging(self):
        """
        Configure the system logger to be used by this program.

        Takes no parameters and returns nothing.
        """
        filename = os.path.join(self._phish_config.config['system']['log_path'], 'system.log')
        dirname = os.path.dirname(filename)
        os.makedirs(dirname, exist_ok=True)
        logging.basicConfig(filename=filename,
                            level=logging.INFO, format="%(asctime)s: %(levelname)s: %(message)s")

    def _run(self):
        """
        Handler and primary interface that solicits user for a desired action and then launches it.
        """
        while True:
            tqdm.tqdm.write(BANNER)
            tqdm.tqdm.write(MAIN_MENU)
            try:
                selection = int(input("Please make a selection [1-6]: "))
            except ValueError:
                tqdm.tqdm.write("Invalid selection - please select a number 1 through"
                                " 6 and press enter.")
                continue

            if selection == 1:
                try:
                    PhishPredictor()(mode='certstream')
                except IOError as error:
                    # Active classifier doesn't exist, error msg tells user to train one.
                    tqdm.tqdm.write("{}".format(error))
                    continue
            elif selection == 2:
                try:
                    PhishPredictor()(mode='manual')
                except IOError as error:
                    # Active classifier doesn't exist, error msg tells user to train one.
                    tqdm.tqdm.write("{}".format(error))
                    continue
            elif selection == 3:
                self._manage_classifiers()
            elif selection == 4:
                self._train_classifier()
            elif selection == 5:
                self._phish_config.print_config()
            elif selection == 6:
                tqdm.tqdm.write("[+] Exiting...")
                sys.exit(0)
            else:
                tqdm.tqdm.write("Invalid selection - please select a number between 1 and 6.")
                continue

    def _manage_classifiers(self):
        """
        List active classifier, list available classifiers, and prompt user to change
                the active classifier.

        1. Summarize accuracy metrics across all trained classifiers.
        2. Show performance metrics from a single classifier.
        3. Change the active classifier.
        4. Delete a classifier.
        5. Return to the main menu.
        """
        while True:
            # List trained classifiers, if any. Return to main menu if no classifiers found.
            available_classifiers = self._phish_db.available_classifiers()
            active_classifier = self._phish_config.active_classifier
            if not available_classifiers:
                tqdm.tqdm.write("[-] There are no classifiers currently trained"
                                " - please train one.")
                return

            # List the active classifier and any other available classifiers.
            if len(available_classifiers) == 1 and active_classifier in available_classifiers:
                tqdm.tqdm.write("[+] The activated classifier, {}, is the only"
                                " one trained.".format(active_classifier))
            else:
                tqdm.tqdm.write("[+] Active classifier: {}".format(active_classifier))
                tqdm.tqdm.write("[+] Other available classifiers:")
                for clf in available_classifiers:
                    if clf != active_classifier:
                        tqdm.tqdm.write("\t- {}".format(clf))

            # If user is this far, they have more than one classifier trained. Let them decide what
            # to do next.
            tqdm.tqdm.write(CLASSIFIERS_MENU)
            try:
                selection = int(input("Please make a selection [1-5]: "))
            except ValueError:
                tqdm.tqdm.write("Invalid input - please select a number 1 through 5"
                                " and press enter.")
                continue
            else:
                if selection < 1 and selection > 5:
                    tqdm.tqdm.write("Invalid selection - please select a number 1 through 5"
                                    " and press enter.")
                    continue

            if selection == 1:
                self._metrics_summary(available_classifiers)
            elif selection == 2:
                self._single_classifier_metrics()
            elif selection == 3:
                self._change_classifier(available_classifiers)
            elif selection == 4:
                self._delete_classifier()
            elif selection == 5:
                tqdm.tqdm.write("[+] Returning to main menu.")
                return

    def _metrics_summary(self, available_classifiers):
        """
        Provides key metrics from all trained classifiers in the database, i.e.
        true positive rates, precision, recall, AUC score, etc.

        Args:
            available_classifiers (list): Trained classifiers in database.
        """
        # Fetch all the classifiers from the DB which contain accuracy metrics.
        classifiers = []
        for classifier_name in available_classifiers:
            classifier = self._phish_db.fetch_classifier(classifier_name)
            classifiers.append({classifier_name: classifier[classifier_name]['metrics']})

        # Create a list of dictionaries for each metric you want to capture and display to user.
        results = {}
        results['Training Set Size'] = {}
        results['Training Set Accuracy'] = {}
        results['Feature Vector Size'] = {}
        results['Test Set Accuracy'] = {}
        results['True Positive Rate [50%]'] = {}
        results['False Positive Rate [50%]'] = {}
        results['Precision [50%]'] = {}
        results['Recall [50%]'] = {}
        results['AUC [50%]'] = {}

        for classifier in classifiers:
            for name, values in classifier.items():
                results['Training Set Size'][name] = \
                        sum(values['info']['training_samples'].values())
                results['Feature Vector Size'][name] = values['info']['feature_vector_size']
                results['Training Set Accuracy'][name] = \
                        values['accuracy']['training_set_accuracy']
                results['Test Set Accuracy'][name] = values['accuracy']['test_set_accuracy']
                results['True Positive Rate [50%]'][name] = \
                        values['accuracy']['true_positive_rate']
                results['False Positive Rate [50%]'][name] = \
                        values['accuracy']['false_positive_rate']
                results['Precision [50%]'][name] = values['accuracy']['precision']
                results['Recall [50%]'][name] = values['accuracy']['recall']
                results['AUC [50%]'][name] = values['accuracy']['auc_score']

        tqdm.tqdm.write("[+] Summary of classifier accuracy metrics:")
        for chart_name, chart_values in results.items():
            tqdm.tqdm.write("\n[--- {} ---]".format(chart_name))
            for clf, score in sorted(chart_values.items(), key=lambda x: x[1], reverse=True):
                tqdm.tqdm.write("{}\t{}".format(score, clf))
        tqdm.tqdm.write("\n[+] Completed.")

    def _single_classifier_metrics(self):
        """
        Solicits user for the name of a trained classifier and prints metrics.
        """
        while True:
            classifier_name = input("Please enter the name of the classifier you want"
                                    " accuracy metrics from: ")
            # Make sure it's in the database.
            if classifier_name not in self._phish_db.available_classifiers():
                tqdm.tqdm.write("[-] Sorry, classifier not found in the database."
                                " Please try again.")
                continue

            # Verified it's in the database - go fetch it.
            artifacts = self._phish_db.fetch_classifier(classifier_name)
            tqdm.tqdm.write("[+] Accuracy metrics for classifier {}:".format(classifier_name))
            tqdm.tqdm.write(json.dumps(artifacts[classifier_name]['metrics'], indent=4))
            break

    def _change_classifier(self, available_classifiers):
        """
        Reach out to the config and change the active classifier.

        Args:
            available_classifiers (list): Classifiers available to use in the DB.
        """
        # If there's only one classifier trained, return to main menu.
        if len(available_classifiers) <= 1:
            return

        # Prompt the user for a classifier name.
        while True:
            classifier_name = input("Please enter the name of the classifier you'd"
                                    " like to activate: ").lower()
            try:
                self._phish_config.active_classifier = classifier_name
                break
            except ValueError as error:
                # Only way this would happen is if they fat-fingered the classifier name.
                tqdm.tqdm.write("[-] An error occurred during activation: {}".format(error))
                continue

    def _delete_classifier(self):
        """
        Reach out to the database and delete a trained classifier.
        """
        while True:
            classifier_name = input("Please enter the name of the classifier you'd"
                                    " like to delete: ").lower()

            # Make sure it's in the database.
            if classifier_name not in self._phish_db.available_classifiers():
                tqdm.tqdm.write("[-] Sorry, classifier not found in the database."
                                " Please try again.")
                continue

            # Verified it's in the database - delete it.
            self._phish_db.delete_classifier(classifier_name)
            break

    def _train_classifier(self):
        """
        Train classifier, compute metrics, and prompt the user for two decisions:
            - keep the classifier? y/n
                - if yes, ask user to name it.
                - validate name is available in the database, then write metrics and classifier.
            - activate the classifier? y/n
                - if yes, update the active classifier name in the config with the new name.
        """
        # In the future, could make a recommendation on which classifier to deploy.
        artifacts = PhishTrainer().generate_model()
        tqdm.tqdm.write("The metrics from the newly trained classifier are as follows:")
        tqdm.tqdm.write(json.dumps(artifacts['metrics'], indent=4))

        while True:
            keep = input("Would you like to keep the classifier? [y/N] ").lower()
            if keep not in VALID_ANSWERS:
                tqdm.tqdm.write("Sorry, please respond with 'yes' or 'no'.")
                continue
            else:
                # Got a good answer - break out of this and proceed.
                break

        if keep in YES_ANSWERS:
            # Prompt the user for a classifier name, validate against DB to ensure it's available.
            # while loop or try/except.
            while True:
                classifier_name = input("Please enter a name (no spaces) for the"
                                        " classifier: ").lower()

                # Check for spaces.
                if ' ' in classifier_name:
                    tqdm.tqdm.write("Sorry, a space was found in the name. Please try again.")
                    continue

                # Check to see if this name is available in the database.
                for clf in self._phish_db.available_classifiers():
                    if clf == classifier_name:
                        overwrite = input("Sorry, a classifier with the same name already"
                                          " exists in the database. Would you like to "
                                          "overwrite it? [y/N]".lower())
                        if overwrite in VALID_ANSWERS:
                            # Delete existing classifier.
                            self._phish_db.delete_classifier(classifier_name)
                        else:
                            # User doesn't want to overwrite but wants to keep the classifier. Let
                            # them pick a new name, don't break.
                            continue

                # No spaces and name is available - proceed with persisting to database.
                artifacts['classifier_name'] = classifier_name
                self._phish_db.save_classifier(artifacts)
                break
        else:
            tqdm.tqdm.write("[+] Not saving - returning to main menu.")
            return

        # Only way to get this far is by saving a classifier wanted by the user.
        # Now check to see if they want to activate it.
        while True:
            activate = input("Would you like to activate the classifier? [y/N] ").lower()
            if keep not in VALID_ANSWERS:
                tqdm.tqdm.write("Sorry, please respond with 'yes' or 'no'.")
                continue
            else:
                # Got a good answer - break out of this and proceed.
                break

        if activate in YES_ANSWERS:
            try:
                self._phish_config.active_classifier = classifier_name
            except ValueError as error:
                tqdm.tqdm.write("[-] An error occurred during activation: {}".format(error))
        else:
            tqdm.tqdm.write("[+] Not activating - returning to main menu.")

if __name__ == '__main__':
    PhishCLI()
