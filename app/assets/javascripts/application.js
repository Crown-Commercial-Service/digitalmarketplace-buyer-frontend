/*
  The following comments are parsed by Gulp include
  (https://www.npmjs.com/package/gulp-include) which uses
  Sprockets-style (https://github.com/sstephenson/sprockets)
  directives to concatenate multiple Javascript files into one.
*/
//= include ../../../node_modules/govuk_frontend_toolkit/javascripts/vendor/polyfills/bind.js
//= include ../../../node_modules/jquery/dist/jquery.js
//= include ../../../node_modules/hogan.js/web/builds/3.0.2/hogan-3.0.2.js
//= include ../../../node_modules/scrolldepth/jquery.scrolldepth.js
//= include ../../../node_modules/digitalmarketplace-frontend-toolkit/toolkit/javascripts/option-select.js
//= include ../../../node_modules/digitalmarketplace-frontend-toolkit/toolkit/javascripts/support.js
//= include ../../../node_modules/digitalmarketplace-frontend-toolkit/toolkit/javascripts/live-search.js
//= include ../../../node_modules/digitalmarketplace-frontend-toolkit/toolkit/javascripts/list-entry.js
//= include ../../../node_modules/digitalmarketplace-frontend-toolkit/toolkit/javascripts/clear-filters.js
//= include ../../../node_modules/digitalmarketplace-frontend-toolkit/toolkit/javascripts/word-counter.js
//= include ../../../node_modules/digitalmarketplace-frontend-toolkit/toolkit/javascripts/validation.js
//= include ../../../node_modules/digitalmarketplace-frontend-toolkit/toolkit/javascripts/report-a-problem.js
//= include ../../../node_modules/govuk_frontend_toolkit/javascripts/govuk/selection-buttons.js
//= include ../../../node_modules/govuk_frontend_toolkit/javascripts/govuk/shim-links-with-button-role.js
//= include ../../../node_modules/digitalmarketplace-frontend-toolkit/toolkit/javascripts/shim-links-with-button-role.js
//= include ../../../node_modules/digitalmarketplace-frontend-toolkit/toolkit/javascripts/show-hide-content.js
//= include _analytics.js'
//= include _onready.js'
//= include _selection-buttons.js

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
