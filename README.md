# Digital Marketplace Buyer Frontend

Frontend buyer application for the digital marketplace.

- Python app, based on the [Flask framework](http://flask.pocoo.org/)

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

```pip install -r requirements.txt```

### Run the tests

```
./scripts/run_tests.sh
```

### Run the development server

To run the Buyer Frontend App for local development you can use the convenient run 
script, which sets the required environment variables to defaults if they have
not already been set:

```
./scripts/run_app.sh
```

If you want the app to be available on the network, you need to set the `DM_HOST` environment variable to '0.0.0.0':

```
DM_HOST='0.0.0.0' ./scripts/run_app.sh
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
