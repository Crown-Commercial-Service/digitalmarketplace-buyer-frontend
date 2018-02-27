/*
  The following comments are parsed by Gulp include
  (https://www.npmjs.com/package/gulp-include) which uses
  Sprockets-style (https://github.com/sstephenson/sprockets)
  directives to concatenate multiple Javascript files into one.
*/
//= require ../../../node_modules/govuk_frontend_toolkit/javascripts/vendor/polyfills/bind.js
//= require ../../../node_modules/jquery/dist/jquery.js
//= require ../../../node_modules/hogan.js/web/builds/3.0.2/hogan-3.0.2.js
//= require ../../../node_modules/scrolldepth/jquery.scrolldepth.js
//= require ../../../node_modules/digitalmarketplace-frontend-toolkit/toolkit/javascripts/option-select.js
//= require ../../../node_modules/digitalmarketplace-frontend-toolkit/toolkit/javascripts/support.js
//= require ../../../node_modules/digitalmarketplace-frontend-toolkit/toolkit/javascripts/live-search.js
//= require ../../../node_modules/digitalmarketplace-frontend-toolkit/toolkit/javascripts/list-entry.js
//= require ../../../node_modules/digitalmarketplace-frontend-toolkit/toolkit/javascripts/clear-filters.js
//= require ../../../node_modules/digitalmarketplace-frontend-toolkit/toolkit/javascripts/word-counter.js
//= require ../../../node_modules/digitalmarketplace-frontend-toolkit/toolkit/javascripts/validation.js
//= require ../../../node_modules/digitalmarketplace-frontend-toolkit/toolkit/javascripts/report-a-problem.js
//= require ../../../node_modules/govuk_frontend_toolkit/javascripts/govuk/selection-buttons.js
//= require ../../../node_modules/govuk_frontend_toolkit/javascripts/govuk/shim-links-with-button-role.js
//= require ../../../node_modules/digitalmarketplace-frontend-toolkit/toolkit/javascripts/shim-links-with-button-role.js
//= require ../../../node_modules/digitalmarketplace-frontend-toolkit/toolkit/javascripts/show-hide-content.js
//= require ../../../node_modules/digitalmarketplace-frontend-toolkit/toolkit/javascripts/user-research-consent-banner.js
//= require _analytics.js'
//= require _onready.js'
//= require _selection-buttons.js

(function(GOVUK, GDM) {

  "use strict";

  var module;

  if(typeof console === 'undefined') {
    console = {
      log: function () {},
      time: function () {},
      timeEnd: function () {}
    };
  }

  if (
    (GDM.debug = !window.location.href.match(/gov.uk/) && !window.jasmine)
  ) {
    console.log(
      "%cDebug mode %cON",
      "color:#550; background:yellow; font-size: 11pt",
      "color:yellow; background: #550;font-size:11pt"
    );
    if (typeof console.time !== "undefined") console.time("Modules loaded");
  }

  // Initialise our modules
  for (module in GDM) {

    if (GDM.debug && module !== "debug") {
      console.log(
        "%cLoading module %c" + module,
        "color:#6a6; background:#dfd; font-size: 11pt",
        "color:#dfd; background:green; font-size: 11pt"
      );
    }

    if ("function" === typeof GDM[module].init) {
      // If a module has an init() method then we want that to be called here
      GDM[module].init();
    } else if ("function" === typeof GDM[module]) {
      // If a module doesn't have an interface then call it directly
      GDM[module]();
    }

  }

  GOVUK.GDM = GDM;

  if (GDM.debug && typeof console.timeEnd !== "undefined") console.timeEnd("Modules loaded");

}).apply(this, [GOVUK||{}, GOVUK.GDM||{}]);
