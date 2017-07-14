# Digital Marketplace Buyer Frontend

[![Coverage Status](https://coveralls.io/repos/alphagov/digitalmarketplace-buyer-frontend/badge.svg?branch=master&service=github)](https://coveralls.io/github/alphagov/digitalmarketplace-buyer-frontend?branch=master)
[![Requirements Status](https://requires.io/github/alphagov/digitalmarketplace-buyer-frontend/requirements.svg?branch=master)](https://requires.io/github/alphagov/digitalmarketplace-buyer-frontend/requirements/?branch=master)

Frontend buyer application for the digital marketplace.

- Python app, based on the [Flask framework](http://flask.pocoo.org/)

## Quickstart

Install [Virtualenv](https://virtualenv.pypa.io/en/latest/)
```
sudo easy_install virtualenv
```

Install dependencies, run migrations and run the app
```
make run-all
````

## Setup

Install [Virtualenv](https://virtualenv.pypa.io/en/latest/)

```
sudo easy_install virtualenv
```

The buyer frontend app requires access to both the API (for service pages) and
to the search API (for search results). The location and access tokens for 
these services is set with environment variables.


For development you can either point the environment variables to use the 
preview environment's `API` and `Search API` boxes, or use local API instances if 
you have them running:

```
export DM_DATA_API_URL=http://localhost:5000
export DM_DATA_API_AUTH_TOKEN=<auth_token_accepted_by_api>
export DM_SEARCH_API_URL=http://localhost:5001
export DM_SEARCH_API_AUTH_TOKEN=<auth_token_accepted_by_search_api>
```

Where `DM_DATA_API_AUTH_TOKEN` is a token accepted by the Data API 
instance pointed to by `DM_API_URL`, and `DM_SEARCH_API_AUTH_TOKEN` 
is a token accepted by the Search API instance pointed to by `DM_SEARCH_API_URL`.

### Create and activate the virtual environment

```
virtualenv ./venv
source ./venv/bin/activate
```

### Upgrade dependencies

Install new Python dependencies with pip

```pip install -r requirements-dev.txt```

[Install frontend dependencies](https://github.com/alphagov/digitalmarketplace-buyer-frontend#front-end) with npm and gulp

```
npm install
```

### Run the tests

To run the whole testsuite:

```
make test
```

To only run the JavaScript tests:

```
npm test
```

### Run the development server

To run the Buyer Frontend App for local development you can use the convenient run 
script, which sets the required environment variables to defaults if they have
not already been set:

```
make run-app
```

More generally, the command to start the server is:
```
python application.py runserver
```

The buyer app runs on port 5002 by default. Use the app at [http://127.0.0.1:5002/](http://127.0.0.1:5002/)

### Updating application dependencies

`requirements.txt` file is generated from the `requirements-app.txt` in order to pin
versions of all nested dependecies. If `requirements-app.txt` has been changed (or
we want to update the unpinned nested dependencies) `requirements.txt` should be
regenerated with

```
make freeze-requirements
```

`requirements.txt` should be commited alongside `requirements-app.txt` changes.

### Using FeatureFlags

To use feature flags, check out the documentation in (the README of)
[digitalmarketplace-utils](https://github.com/alphagov/digitalmarketplace-utils#using-featureflags).

## Front-end

Front-end code (both development and production) is compiled using [Node](http://nodejs.org/) and [Gulp](http://gulpjs.com/).

### Requirements

You need Node (minimum version of 0.10.0, maximum version 0.12.x), which will also get you [NPM](npmjs.org), Node's package management tool. 

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
- `npm run frontend-build:watch` (watch all frontend+framework files & rebuild when anything changes)
- `npm run frontend-install` (install all non-NPM dependancies)

Note: `npm run frontend-install` is run automatically as a post-install task when you run `npm install`.
