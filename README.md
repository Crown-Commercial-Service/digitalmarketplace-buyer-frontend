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

Set the required environment variables (for dev use local API instance if you 
have it running):

```
export DM_API_URL=https://api.digitalmarketplace.service.gov.uk
export DM_API_BEARER=<bearer_token>
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

```
python application.py runserver
```

The buyer app runs on port 5002. Use the app at [http://127.0.0.1:5002/](http://127.0.0.1:5002/)

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

#### Non-NPM dependencies

Running `npm install` will also install all the required dependencies not available as NPM modules. At present this is:

- the [Digital Marketplace front-end toolkit](https://github.com/alphagov/digitalmarketplace-frontend-toolkit)
- the [GOVUK Template](https://github.com/alphagov/govuk_template)

These dependencies are installed by the `./scripts/install_frontend_dependencies.py` script which is run after the NPM modules are installed.

### Static asset locations

The base static asset files should be kept in `app/assets`. The results of compilation are put into `app/static`.

You can compile the assets in 2 modes: 'development' and 'production' like so:

#### Compiling for development

```
node_modules/gulp/bin/gulp.js build:development
```

#### Compiling for production 

```
node_modules/gulp/bin/gulp.js build:production
```
