# StreamingPhish

This is a utility that uses supervised machine learning to detect phishing domains from the Certificate Transparency log network. The firehose of domain names and SSL certificates are made available thanks to the certstream network (certstream.calidog.io). All of the data required for training the initial predictive model is included in this project as well.

Also included is a Jupyter notebook to help explain each step of the supervised machine learning lifecycle (as it pertains to this project).

## Overview

This application consists of three main components:

### Jupyter notebook
  - Demonstrates how to train a phishing classifier from start to finish.
  
### CLI utility
  - Trains classifiers and evaluates domains in manual mode or against the Certificate Transparency log network (via certstream).
  
### Database
  - Stores trained classifiers, performance metrics, and code for feature extraction.

Each segment has been functionally decomposed into its own Docker container. The application is designed to be built and operated via Docker Compose.

## Install and Operational Instructions

[Visit the wiki section](https://github.com/wesleyraptor/streamingphish/wiki) for detailed instructions on how to install and use the Jupyter notebook and CLU utility. Wiki pages for specific topics are listed below as well.

- [Setup and Install](https://github.com/wesleyraptor/streamingphish/wiki/Setup-and-Install)
- [Jupyter Notebook](https://github.com/wesleyraptor/streamingphish/wiki/Jupyter-Notebook)
- [CLI Utility](https://github.com/wesleyraptor/streamingphish/wiki/CLI-Utility)
  - [Training and Retraining Classifiers](https://github.com/wesleyraptor/streamingphish/wiki/Training-and-Retraining)
  - [Classifier Management](https://github.com/wesleyraptor/streamingphish/wiki/Classifier-Management)

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
