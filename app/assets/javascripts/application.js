/*
  The following comments are parsed by Gulp include
  (https://www.npmjs.com/package/gulp-include) which uses
  Sprockets-style (https://github.com/sstephenson/sprockets)
  directives to concatenate multiple Javascript files into one.
*/
//= require ../../../node_modules/jquery/dist/jquery.js
//= require ../../../node_modules/scroll-depth/jquery.scrolldepth.js
//= require ../../../node_modules/govuk-frontend/govuk/all.js
//= require ../../../node_modules/digitalmarketplace-govuk-frontend/digitalmarketplace/all.js
//= require _onready.js'
//= require _live-search.js

GOVUKFrontend.initAll();
DMGOVUKFrontend.initAll();
