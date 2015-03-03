# Digital Marketplace Thermos

Experimental frontend spike for Digital Marketplace.

- Python app, based on the [Flask framework](http://flask.pocoo.org/)

## Setup

Install [Virtualenv](https://virtualenv.pypa.io/en/latest/)

```
sudo easy_install virtualenv
```

Install [elasticsearch](http://www.elasticsearch.org/)

```
brew update
brew install elasticsearch
```

Set the required environment variables (for dev use local API instances if you 
have them running):

```
export DM_API_URL=http://localhost:5000
export DM_API_BEARER=<bearer_token>
export DM_SEARCH_API_URL=http://localhost:5001
export DM_SEARCH_API_BEARER=<bearer_token>
```

### Create and activate the virtual environment

```
virtualenv ./venv
source ./venv/bin/activate
```

### Upgrade dependencies

Install new Python dependencies with pip

```pip install -r requirements.txt```

### Insert G6 services into elasticsearch index

Start elasticsearch

```
elasticsearch
```

Index G6 services into your local elasticsearch index:

```
./scripts/index-g6-in-elasticsearch.py http://localhost:9200/services https://api-origin.digitalmarketplace.service.gov.uk/services <api_bearer_token>
```

(Ideally we would use `api.digitalmarketplace.service.gov.uk` but CloudFront doesn't like the Python HTTP client.)

### Run the tests

```
./scripts/run_tests.sh
```

### Run the development server

To run the Buyer Frontend App for local development you can use the convenient run 
script, which sets the required environment variables to defaults if they have
not already been set: 
```
./run_buyer_frontend.sh
```

More generally, the command to start the server is:
```
python application.py runserver
```

The buyer app runs on port 5002 by default. Use the app at [http://127.0.0.1:5002/](http://127.0.0.1:5002/)

## Front-end

Front-end code (both development and production) is compiled using [Node](http://nodejs.org/) and [Gulp](http://gulpjs.com/).

### Requirements

You need Node, minimum version of 0.10.0, which will also get you [NPM](npmjs.org), Node's package management tool. 

To check the version you're running, type:

```
node --version
```

### Installation

To install the required Node modules, type:

```
npm install
```

## Frontend tasks

[NPM](https://www.npmjs.org/) is used for all frontend build tasks. The commands available are:

- `npm run frontend-build:development` (compile the frontend files for development)
- `npm run frontend-build:production` (compile the frontend files for production)
- `npm run frontend-build:watch` (watch all frontend files & rebuild when anything changes)
- `npm run frontend-install` (install all non-NPM dependancies)

Note: `npm run frontend-install` is run automatically as a post-install task when you run `npm install`.
