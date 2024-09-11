"""
This module is dedicated to training classifiers. It loads training data, whose paths
are defined in the configuration, calls PhishFeatures to extract features, trains
a model, and produces metrics. The PhishTrainer class trains a classifier and returns
it along with metrics to the caller (cli.py).

See the PhishTrainer class for more details.
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
import pickle
from datetime import datetime
from collections import OrderedDict

import tqdm
import pandas as pd
import numpy as np
from bson.binary import Binary
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.metrics import roc_curve
from sklearn.metrics import precision_recall_curve
from sklearn.metrics import confusion_matrix

from .features import PhishFeatures
from .configuration import PhishConfig

class PhishTrainer:
    """
    Handler for training a classifier and writing artifacts (feature extractor, feature
        vector, and actual classifier) to the database.
    """
    def __init__(self):
        self._phish_config = PhishConfig()
        self._features = PhishFeatures(self._phish_config.config['data'])

    def generate_model(self):
        """
        Trains model, calls _generate_metrics, solicits user for input.
            - if they want to keep it --> write to DB.
            - if they want to activate it --> write to config.
        """
        training_data = self._load_training_data()
        tqdm.tqdm.write("[*] Computing features...")
        training_features = self._features.compute_features(training_data.keys(), values_only=False)
        self._train_model(training_features, training_data.values())
        self._compute_metrics()
        artifacts = self._generate_artifacts()
        return artifacts

    def _train_model(self, features, labels_list):
        """
        Train model with features and labels generated from training set.

        Args:
            features (dictionary): Two keys - names and values, where names holds the feature
                vector and values holds the features from each FQDN from training.
            labels_list (list): Labels for training data (0 = benign, 1 = phishing).
        """
        # Convert to dataframe.
        features_df = pd.DataFrame.from_records(features['values'], columns=features['names'])

        # Save feature vector to the class object.
        self._feature_vector = features['names']

        # Convert labels list to numpy array. Assigning to self because I need to compute how
        # many samples from each class were present in _compute_metrics.
        self._labels = np.fromiter(labels_list, dtype=float)

        # Split training data from evaluation data. Assigning to class object because we'll use them
        # to help compute metrics against the classifier we're about to train.
        self._x_train, self._x_test, self._y_train, self._y_test = train_test_split(
            features_df.values, self._labels, random_state=2)

        # Train the model, son. Go on now.
        self._classifier = LogisticRegression(C=10).fit(self._x_train, self._y_train)
        tqdm.tqdm.write("[+] Training complete.")

    def _compute_metrics(self):
        """
        Computes metrics from the newly trained classifier important to evaluating
        the classifier's performance and accuracy, i.e.:
            accuracy
                TPR, FPR, precision, recall, AUC, confusion matrix,
                accuracy against training/test
            info
                algorithm, parameters, date/time, training set makeup
            performance
                training speed, analysis speed

        Args:
            None, as all artifacts needed for computation are assigned as class attributes.
        """
        tqdm.tqdm.write("[*] Computing classifier metrics...")
        result = {}

        # First, gather info about the trained classifier.
        result['info'] = {}
        result['info']['algorithm'] = str(self._classifier).split('(')[0]
        result['info']['parameters'] = self._classifier.get_params()
        result['info']['training_date'] = str(datetime.now())
        result['info']['training_samples'] = {}
        result['info']['training_samples']['not_phishing'] = np.count_nonzero(self._labels == 0)
        result['info']['training_samples']['phishing'] = np.count_nonzero(self._labels == 1)
        result['info']['feature_vector_size'] = len(self._feature_vector)

        # Next, grab accuracy info.
        result['accuracy'] = {}
        result['accuracy']['training_set_accuracy'] = "{:.4f}".format(self._classifier.score(
            self._x_train, self._y_train))
        result['accuracy']['test_set_accuracy'] = "{:.4f}".format(self._classifier.score(
            self._x_test, self._y_test))

        # Accuracy - TPR, FPR, AUC score.
        # Also consider that not all algorithms support the predict_proba function.
        fpr, tpr, thresholds = roc_curve(self._y_test, self._classifier.predict_proba(
            self._x_test)[:, 1])
        close_zero = np.argmin(np.abs(thresholds - 0.5))
        result['accuracy']['true_positive_rate'] = "{:.4f}".format(tpr[close_zero])
        result['accuracy']['false_positive_rate'] = "{:.4f}".format(fpr[close_zero])
        auc = roc_auc_score(self._y_test, self._classifier.predict_proba(self._x_test)[:, 1] > 0.5)
        result['accuracy']['auc_score'] = "{:.4f}".format(auc)

        # Accuracy - precision and recall.
        precision, recall, thresholds = \
            precision_recall_curve(self._y_test, self._classifier.predict_proba(self._x_test)[:, 1])
        close_zero = np.argmin(np.abs(thresholds - 0.5))
        result['accuracy']['precision'] = "{:.4f}".format(precision[close_zero])
        result['accuracy']['recall'] = "{:.4f}".format(recall[close_zero])

        # Accuracy - confusion matrix.
        predictions = self._classifier.predict_proba(self._x_test)[:, 1] > 0.5
        confusion = confusion_matrix(self._y_test, predictions)
        result['accuracy']['confusion_matrix'] = confusion.tolist()

        tqdm.tqdm.write("[+] Classifier metrics available.")
        self._metrics = result

    def _generate_artifacts(self):
        """
        Package classifier, feature vector, feature extractor, and metrics into a dict, and return
        to caller.

        Args:
            None, as all artifacts required are already assigned as class attributes.

        Returns:
            artifacts (dictionary): Metrics and binary objects representing classifier.
        """
        artifacts = {}

        # Add metrics.
        artifacts['metrics'] = self._metrics

        # PhishFeatures (extractor), feature vector, and classifier need to be converted
        # to binary form before they can be written to the database.
        artifacts['classifier'] = Binary(pickle.dumps(self._classifier))
        artifacts['feature_extractor'] = Binary(pickle.dumps(self._features))

        return artifacts

    def _load_training_data(self):
        """
        Load the phishing domains and benign domains from disk into python lists.

        Args:
            None, all artifacts available as class attributes.

        Returns:
            training_data (dictionary):  Keys are domain names and values
                are labels (0 = benign, 1 = phishing).
        """
        training_data = OrderedDict()

        # Load domains from all the text files in the benign folder.
        tqdm.tqdm.write("[*] Loading benign data.")
        benign_path = self._phish_config.config['data']['benign_dir']
        for root, dirs, files in os.walk(benign_path):
            files = [f for f in files if not f[0] == "."]
            for f in files:
                with open(os.path.join(root, f)) as infile:
                    for item in infile.readlines():
                        # Safeguard to prevent adding duplicate data to training set.
                        if item not in training_data:
                            training_data[item.strip('\n')] = 0

        # Load domains from all the text files in the malicious folder
        # (this is our 'positive' class).
        tqdm.tqdm.write("[*] Loading malicious data.")
        malicious_path = self._phish_config.config['data']['malicious_dir']
        for root, dirs, files in os.walk(malicious_path):
            files = [f for f in files if not f[0] == "."]
            for f in files:
                with open(os.path.join(root, f)) as infile:
                    for item in infile.readlines():
                        # Safeguard to prevent adding duplicate data to training set.
                        if item not in training_data:
                            training_data[item.strip('\n')] = 1

        tqdm.tqdm.write("[+] Completed loading training data.")
        return training_data
