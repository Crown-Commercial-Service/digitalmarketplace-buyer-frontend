# Digital Marketplace Buyer Frontend

[![Coverage Status](https://coveralls.io/repos/alphagov/digitalmarketplace-buyer-frontend/badge.svg?branch=master&service=github)](https://coveralls.io/github/alphagov/digitalmarketplace-buyer-frontend?branch=master)
![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)

Frontend application for the Digital Marketplace.

- Python app, based on the [Flask framework](http://flask.pocoo.org/)

This app contains:
 
- Digital Marketplace's public pages
- the G-Cloud buyer journey

## Quickstart

It's recommended to use the [DM Runner](https://github.com/alphagov/digitalmarketplace-runner)
tool, which will install and run the app as part of the full suite of apps.

If you want to run the app as a stand-alone process, clone the repo then run:

```
make run-all
````

This command will install dependencies and start the app.

By default, the app will be served at [http://127.0.0.1:5002](http://127.0.0.1:5002/).
This can be changed by setting the `DM_BUYER_PORT` environment variable.
 

### API dependencies

(If you are using DM Runner you can skip this section.)

The Buyer Frontend app requires access to both the API app (for service pages) and
to the search API app (for search results). The location and access tokens for
these services is set with environment variables in `config.py`.

For development, you can either point the environment variables to use the
preview environment's `API` and `Search API` boxes, or use local API instances if 
you have them running:

```
export DM_DATA_API_URL=http://localhost:5000
export DM_DATA_API_AUTH_TOKEN=<auth_token_accepted_by_api>
export DM_SEARCH_API_URL=http://localhost:5009
export DM_SEARCH_API_AUTH_TOKEN=<auth_token_accepted_by_search_api>
```

Where `DM_DATA_API_AUTH_TOKEN` is a token accepted by the Data API 
instance pointed to by `DM_API_URL`, and `DM_SEARCH_API_AUTH_TOKEN` 
is a token accepted by the Search API instance pointed to by `DM_SEARCH_API_URL`.

## Testing

Run the full test suite:

```
make test
```

To only run the Python or Javascript tests:

```
make test-python
make test-javascript
```

To run the `flake8` linter:

```
make test-flake8
```

### Updating Python dependencies

`requirements.txt` file is generated from the `requirements.in` in order to pin
versions of all nested dependencies. If `requirements.in` has been changed (or
we want to update the unpinned nested dependencies) `requirements.txt` should be
regenerated with

```
make freeze-requirements
```

`requirements.txt` should be committed alongside `requirements.in` changes.

## Frontend assets

Front-end code (both development and production) is compiled using [Node](http://nodejs.org/) and [Gulp](http://gulpjs.com/).

### Requirements

You need Node (try to install the version we use in production -
 see the [base docker image](https://github.com/alphagov/digitalmarketplace-docker-base/blob/master/base.docker)).

To check the version you're running, type:

```
node --version
```

### Frontend tasks

[npm](https://docs.npmjs.com/cli/run-script) is used for all frontend build tasks. The commands available are:

- `npm run frontend-build:development` (compile the frontend files for development)
- `npm run frontend-build:production` (compile the frontend files for production)
- `npm run frontend-build:watch` (watch all frontend+framework files & rebuild when anything changes)

### Updating NPM dependencies

Update the relevant version numbers in `package.json`, then run

```
npm install
```

Commit the changes to `package.json` and `package-lock.json`.

You can also run `npm audit fix` to make minor updates to `package-lock.json`.

## Contributing

This repository is maintained by the Digital Marketplace team at the [Government Digital Service](https://github.com/alphagov).

If you have a suggestion for improvement, please raise an issue on this repo.

### Reporting Vulnerabilities

If you have discovered a security vulnerability in this code, we appreciate your help in disclosing it to us in a
responsible manner.

Please follow the [GDS vulnerability reporting steps](https://github.com/alphagov/.github/blob/master/SECURITY.md),
giving details of any issue you find. Appropriate credit will be given to those reporting confirmed issues.

## Licence

Unless stated otherwise, the codebase is released under [the MIT License][mit].
This covers both the codebase and any sample code in the documentation.

The documentation is [&copy; Crown copyright][copyright] and available under the terms
of the [Open Government 3.0][ogl] licence.

[mit]: LICENCE
[copyright]: http://www.nationalarchives.gov.uk/information-management/re-using-public-sector-information/uk-government-licensing-framework/crown-copyright/
[ogl]: http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/
