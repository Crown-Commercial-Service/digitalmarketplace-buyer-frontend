# Digital Marketplace Buyer Frontend

Frontend buyer application for the digital marketplace.

- Python app, based on the [Flask framework](http://flask.pocoo.org/)

## Setup

Install [Virtualenv](https://virtualenv.pypa.io/en/latest/)

```
sudo easy_install virtualenv
```

Mac users may need to install cairo and pango (dependencies for weasyprint, the PDF generator).
```
brew install cairo
brew install pango
```

### Set environment variables

The buyer frontend app requires access to both the API (for service pages) and
to the search API (for search results). The location and access tokens for 
these services is set with environment variables.


For development you can either point the environment variables to use the 
preview environment's `API` and `Search API` boxes, or use local API instances if 
you have them running:

```
export DM_DATA_API_URL=http://localhost:5000
export DM_DATA_API_AUTH_TOKEN=<auth_token_accepted_by_api>
export AWS_ACCESS_KEY_ID=<access key ID for AWS>
export AWS_SECRET_ACCESS_KEY=<secret key corresponding to the above key ID>
export AWS_DEFAULT_REGION=<region for AWS>
```

Where `DM_DATA_API_AUTH_TOKEN` is a token accepted by the Data API 
instance pointed to by `DM_API_URL`.

The AWS key is currently used for email sending.

### Create and activate the virtual environment

Create the virtual environment:

```
virtualenv ./venv
```

Activate it:
```
source ./venv/bin/activate
```

You should now see `(venv)` in your prompt.  The virtual environment should only need to be created once, but it needs
to be activated again if you switch terminal (or repository).

### Upgrade dependencies

Install new Python dependencies with pip

```pip install -r requirements_for_test.txt```

[Install frontend dependencies](https://github.com/alphagov/digitalmarketplace-buyer-frontend#front-end) with npm and gulp

```
npm install
npm run frontend-build:production
```

### Run the tests

To run the whole testsuite:

```
./scripts/run_tests.sh
```

To only run the JavaScript tests:

```
npm test
```

### Run the development server

Every time you open a new terminal, you'll need to set the environment variables and activate the Python virtual
environment before you can run the server or tests.

The command to start the server by itself is
```
python application.py runserver
```

The buyer app runs on port 5002 by default. Use the app at [http://127.0.0.1:5002/](http://127.0.0.1:5002/)

If you want to run the other frontends in a local environment, there's a reverse proxy config that unifies them behind one domain.
To use it you need to install lighttpd on your system, then you can run

```
./scripts/reverse_proxy.sh
```

Run the other frontends using the normal `python application.py runserver` commands in other terminals.
The Marketplace should now be available at `http://localhost:8000/marketplace/`

### Using FeatureFlags

To use feature flags, check out the documentation in (the README of)
[digitalmarketplace-utils](https://github.com/alphagov/digitalmarketplace-utils#using-featureflags).

## Front-end

Front-end code (both development and production) is compiled using [Node](http://nodejs.org/) and [Gulp](http://gulpjs.com/).

### Requirements

You need Node (version 5.5.0 recommended), which will also get you [NPM](npmjs.org), Node's package management tool. 

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

## Frontend tests

To run the JavaScript tests, navigate to `spec/javascripts/support/` and open `LocalTestRunner.html` in a browser.

TODO: Add a Gulp task which is run as part of `./scripts/run_tests.sh`.
