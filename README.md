# StreamingPhish

This is a utility that uses supervised machine learning to detect phishing domains from the Certificate Transparency log network. The firehose of domain names and SSL certificates are made available thanks to the certstream network (certstream.calidog.io). All of the data required for training the initial predictive model is included in this project as well.

Also included is a Jupyter notebook to help explain each step of the supervised machine learning lifecycle (as it pertains to this project).

## Getting Started

This application consists of three main components:

1. Jupyter notebook
  - Demonstrates how to train a phishing classifier from start to finish.
2. CLI utility
  - Trains classifiers and evaluates domains in manual mode or against the Certificate Transparency log network (via certstream).
3. Database
  - Stores trained classifiers, performance metrics, and code for feature extraction.

Each segment has been functionally decomposed into its own Docker container. The application is designed to be built and operated via Docker Compose.

#### Prerequisites

The BASH script **install_streamingphish.sh** performs automatic installation on any Linux platform officially supported by Docker CE. It's been tested against the following images from [DigitalOcean](https://www.digitalocean.com/) with no issues:

- Centos 7
- Ubuntu 16.04
- Debian 9.4
- Fedora 27

DigitalOcean droplets, AWS instances, or other cloud-based VMs with at least 2GBs of RAM should do the trick.

#### Installation

```
 git clone https://github.com/wesleyraptor/streamingphish.git
 cd streamingphish/
 sudo ./install_streamingphish.sh
```

Installation via `install_streamingphish.sh` is strongly encouraged. This routine will build the containers and run them in detached mode (running in the background). The output should appear as follows:

```
Creating wes_notebook_1 ... done
Creating wes_db_1       ... done
Creating wes_cli_1      ... done

[+] Successfully built and ran the application in daemon mode.

There are 3 services embedded within this application:
 - db
 - cli
 - notebook

Primary actions:
  1. The Jupyter notebook is currently available at <your_servers_ip_address>:9000.
  2. Run streamingphish CLI utility:
      $ docker-compose exec cli streamingphish

Secondary actions:
  View service state:
   $ docker-compose ps
  Stop all daemon services:
   $ docker-compose down
  Rebuild application and restart services after updating source code:
    $ docker-compose up -d --build
```

Installation on Mac OSX, though not officially supported, should work if docker and docker-compose are already installed. Run the following command to build and start the containers:

```
 sudo docker-compose up -d
 ```

## Operations

### Jupyter Notebook

The Jupyter notebook comes with a default password of **streamingphish**, and should be viewable immediately after installation at:
```
  http://<your_system_ip_address>:9000
```

The default notebook file, **StreamingPhish.ipynb**, is bind-mounted from the host system directly into the container. Any changes to the notebook (or adding additional notebooks) will persist to the host system in the notebooks/ folder regardless of the state of the underlying container.

### CLI Utility

Invoke the CLI utility with the following command:

```
 docker-compose exec cli streamingphish
```

Users should immediately be presented with the main menu:

```
wes@phishtest-4:~$ sudo docker-compose exec cli streamingphish                

   _____ __                            _
  / ___// /_________  ____ _____ ___  (_)
  \__ \/ __/ ___/ _ \/ __ `/ __ `__ \/ / __ \/ __ `/
 ___/ / /_/ /  /  __/ /_/ / / / / / / / / / / /_/ /
/____/\__/_/   \___/\__,_/_/ /_/ /_/_/_/ /_/\__, /
    ____  __    _      __                  /____/
   / __ \/ /_  (_)____/ /
  / /_/ / __ \/ / ___/ __ \
 / ____/ / / / (__  ) / / /
/_/   /_/ /_/_/____/_/ /_/         by Wes Connell
                                      @wesleyraptor


1. Deploy phishing classifier against certstream feed.
2. Operate phishing classifier in manual mode.
3. Manage classifiers (list active classifier and show available classifiers).
4. Train a new classifier.
5. Print configuration.
6. Exit.
  
Please make a selection [1-6]:
```

#### Training a Classifier

The system doesn't include any trained classifiers by default - to start, select option 4 to train one. The metrics from the trained classifier will be printed to the screen as soon as training is complete (and FYI if you're unfamiliar with what the metrics mean, take a look at the accompanying Jupyter notebook). Continue following the instructions to save the classifier, give it a name, and activate it:

```
Please make a selection [1-6]: 4
[*] Loading benign data.
[*] Loading malicious data.
[+] Completed loading training data.
[*] Computing features...
[+] Training complete.
[*] Computing classifier metrics...
[+] Classifier metrics available.
The metrics from the newly trained classifier are as follows:
{
    "info": {
        "feature_vector_size": 467,
        "training_samples": {
            "phishing": 5000,
            "not_phishing": 5000
        },
        "parameters": {
            "penalty": "l2",
            "solver": "liblinear",
            "C": 10,
            "multi_class": "ovr",
            "intercept_scaling": 1,
            "n_jobs": 1,
            "class_weight": null,
            "fit_intercept": true,
            "tol": 0.0001,
            "warm_start": false,
            "verbose": 0,
            "random_state": null,
            "dual": false,
            "max_iter": 100
        },
        "training_date": "2018-03-27 07:18:47.759669",
        "algorithm": "LogisticRegression"
    },
    "accuracy": {
        "precision": "0.9959",
        "training_set_accuracy": "0.9991",
        "auc_score": "0.9915",
        "recall": "0.9871",
        "test_set_accuracy": "0.9916",
        "false_positive_rate": "0.0040",
        "true_positive_rate": "0.9903"
    }
}
Would you like to keep the classifier? [y/N] y
Please enter a name (no spaces) for the classifier: wesley_test_v1
[+] Saved new classifier wesley_test_v1.
Would you like to activate the classifier? [y/N] y
[+] Activated new classifier, wesley_test_v1, in configuration.
```

### Managing Classifiers

Select option 3 of the main menu to view a summary of performance metrics from all trained classifiers, change the active classifier, or delete a trained classifier. The classifier management menu looks like this:

```
[+] Active classifier: better_training_data
[+] Other available classifiers:
        - wesley_v1
        - wesley_test_v2
        - who_dat
        - no_fqdn_keywords

1. Summarize accuracy metrics across all trained classifiers.
2. Show performance metrics from a single classifier.
3. Change the active classifier.
4. Delete a classifier.
5. Return to the main menu.
```

Below is a snippet of what the accuracy metrics might look like after training a few classifiers. The purpose of training additional classifiers is to explore how changes to the independent variables affect classifier performance (i.e. adding new training data, expanding/reducing features, using different algorithms, using different algorithm parameters, etc). One of the perks from building the application with docker-compose is that the classifiers don't disappear even after you make code changes and rebuild the cli container, because the database container stays up the entire time.

```
Please make a selection [1-5]: 1
[+] Summary of classifier accuracy metrics:

[--- Test Set Accuracy ---]
0.9964  wesley_v1
0.9948  no_fqdn_keywords
0.9944  better_training_data
0.9944  wesley_test_v2
0.9936  no_tlds_included

[--- AUC [50%] ---]
0.9964  wesley_v1
0.9948  no_fqdn_keywords
0.9944  better_training_data
0.9944  wesley_test_v2
0.9935  no_tlds_included

[--- Recall [50%] ---]
0.9952  wesley_v1
0.9936  no_fqdn_keywords
0.9928  better_training_data
0.9928  wesley_test_v2
0.9902  no_tlds_included

[--- Precision [50%] ---]
0.9976  wesley_v1
0.9968  better_training_data
0.9968  wesley_test_v2
0.9959  no_tlds_included
0.9952  no_fqdn_keywords

[--- Feature Vector Size ---]
467     wesley_v1
465     better_training_data
465     wesley_test_v2
465     no_fqdn_keywords
414     no_tlds_included

[--- Training Set Accuracy ---]
0.9992  better_training_data
0.9992  wesley_test_v2
0.9989  no_fqdn_keywords
0.9988  wesley_v1
0.9968  no_tlds_included
```
### Operating in Manual Mode

After training a classifier, use option 2 from the main menu to manually evaluate domains via the command line. When finished, type `exit` or `quit` to return to the main menu.

```
Please make a selection [1-6]: 2
[*] Fetching active classifier name from config.
[*] Fetching classifier artifacts from database.
[+] Loaded feature extractor.
[+] Loaded wesley_v1 classifier.
[+] Deploying in manual mode. Type 'exit' or 'quit' at any time to return to the main menu.
FQDN/Host/URL: com-appleid.suspcious.payment-now.forsurenotphishing.com
[PHISHING]: 1.000
FQDN/Host/URL: wvw.pavpal-account-suspended.com
[PHISHING]: 1.000
FQDN/Host/URL: bankofamerica-com.forgot-password.tksqjrhvsrh.ml
[PHISHING]: 1.000
FQDN/Host/URL: exit
[+] Returning to main menu.
```

## Pro Tips

- The configuration file at **cli/config/config.yaml** is used by the CLI tool and defines several criteria, such as:
  - Certstream logging (include issuer CA, include root CA, include log source, etc)
  - Active classifier
  - Data sources for features and training data
  - Classifier thresholds for phishing predictions
- The **training_data/** folder is bind-mounted from the host system directly into the **cli** container. Any changes to the training data, features, keywords, targeted brands, or TLDs will persist to the host system in the **training_data/** folder regardless of the state of the underlying container.
- Fully-qualified domain names (FQDNs) predicted as phishing will be written to a bind-mounted folder named **predictions/**. Log files will be generated in this folder based on the scoring thresholds defined in **cli/config/config.yaml**. The score produced by the classifier when evaluating a host will always be between 0 and 1 (1 == phishing, 0 == benign). FQDNs with higher scores are more likely to be phishing. The default thresholds are as follows:
  - "High" threshold is 0.90 and above
  - "Suspicious" threshold is between 0.90 and 0.75
  - "Low" threshold is between 0.75 and 0.60

  Any FQDN with a score of 0.60 or lower will not be logged.

#### Extending / Modifying Source Code

The code for the CLI utility exists in the directory at **cli/streamingphish/streamingphish/**. Extending or modifying this code will require rebuilding the application. This can be done with the following command:

```
 sudo docker-compose up -d --build
```

The db and notebook containers should remain unchanged, whereas the cli container should be rebuilt.

#### Checking Container State
 
```
 sudo docker-compose ps
```
 
#### Stopping Containers
 
```
 sudo docker-compose down
```

## Components

* [Docker](https://docs.docker.com/install/) - Containers that run the application.
* [Docker Compose](https://docs.docker.com/compose/install/) - Fabric for orchestrating containers and their respective services.
* [Python3](https://www.python.org/downloads/) - Programming language.
* [Scikit-learn](http://scikit-learn.org/stable/) - Open source library for training classifiers using Python. 

## Author

* **Wes Connell**

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE.md](LICENSE.md) file for further details.

## Resources/Acknowledgments

* [Certificate Transparency Log Network](https://www.certificate-transparency.org/what-is-ct) - Framework that aggregates and streams SSL certificates issued by authorities in near real-time.
* [x0rz Phishing Catcher](https://github.com/x0rz/phishing_catcher/) - Phishing detection utility I saw that inspired me to build this project.
* [Calidog Security](https://github.com/CaliDog/certstream-python) - Calidog Security, creators of the certstream library.
* [Phishing Regex Resource](https://github.com/SwiftOnSecurity/PhishingRegex/blob/master/PhishingRegex.txt) - Cherry-picked a few of the phishing words from this list, authored by [SwiftOnSecurity](https://twitter.com/SwiftOnSecurity).
* [PhishTank](https://www.phishtank.com/) - Helped with identifying brands frequently targeted in phishing attacks.
