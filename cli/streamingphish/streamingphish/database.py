"""
Module for interfacing with the database, MongoDB. Classifiers, feature extractors, and their
metrics get stored in the database.

See the PhishDB class for more details on attributes and capabilities.
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


import pickle
import tqdm
import pymongo

# "db" comes from the "db" service in docker-compose.yml.
DB_HOST = 'db'
DB_PORT = 27017
DB_NAME = 'streamingphish'
CLASSIFIERS = 'classifiers'

class PhishDB:
    """
    Represents the database, which is used for storing classifier artifacts (feature vector,
    feature extractor, actual classifier, and metrics.

    The configuration defines an active classifier. Use this class for CRUD operations as it
    pertains to managing the classifiers.

    No public attributes, just public functions like save_classifier, fetch classifier, etc.
    """

    def __init__(self):
        self._db_connection = pymongo.MongoClient(DB_HOST, DB_PORT)
        self._phishing_db = self._db_connection[DB_NAME]
        self._classifiers = self._phishing_db[CLASSIFIERS]

    def save_classifier(self, artifacts):
        """
        Saves classifier, feature extractor, feature vector, and metrics to the database.

        Args:
            artifacts (dictionary): 3 binary objects and a dict storing metrics info.
        """

        # Grab classifier name to use as private key, then delete it from the dictionary.
        name = artifacts['classifier_name']
        del artifacts['classifier_name']

        # Write to the database.
        result = {name: artifacts}
        self._classifiers.insert_one(result)
        tqdm.tqdm.write("[+] Saved new classifier {}.".format(name))

    def delete_classifier(self, classifier_name):
        """
        Deletes a classifier from the database.

        Args:
            classifier_name (string): Name of the classifier to be deleted.
        """
        self._classifiers.delete_many({classifier_name: {"$exists": True}})
        tqdm.tqdm.write("[+] Deleted classifier {}.".format(classifier_name))

    def available_classifiers(self):
        """
        Lists names of classifiers available in the database.

        Returns:
            classifier_names (list): List of all classifier names.
        """
        classifier_names = []
        for clf in self._classifiers.find():
            for key in clf.keys():
                if key != "_id":
                    # This is a classifier name - add to list and return it.
                    classifier_names.append(key)
        return classifier_names

    def verify_classifier_existence(self, classifier):
        """
        Classifier candidate to be saved in config - lets make sure it's available in the DB first.

        Args:
            classifier (string): name of new classifier to be activated.

        Returns:
            True for present, False if not present.
        """
        if classifier not in self.available_classifiers():
            return False
        return True

    def fetch_classifier(self, classifier_name):
        """
        Fetches the name of the classifier to look for in the database.

        Args:
            classifier_name (string): Name of classifier to be fetched.

        Returns:
            result (dictionary): Contains metrics and bytes for classifier, feature vector, etc.
        """
        result = self._classifiers.find_one({classifier_name: {"$exists": True}})
        return result

    @staticmethod
    def restore_python_object(blob):
        """
        Objects like the feature vector, feature exraction object, and classifier are converted to
        a Binary object then patched by pymongo as a bytes instance. This routine restores the
        original object.

        Additional info:
            https://stackoverflow.com/questions/22077720/pymongo-bson-binary-save-and-retrieve

        Also could look into using mongoengine for operations like this.

        Args:
            blob (bytes): Representation of python object to be decoded.

        Returns:
            result (decoded bytes): Could be Index(), PhishFeatures(), LogisticRegression()
        """
        result = pickle.loads(data=blob, encoding='bytes')
        return result
