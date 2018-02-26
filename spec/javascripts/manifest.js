// files are loaded from the /spec/javascripts/support folder so paths are relative to that
var manifest = {
  support : [
    '../../../node_modules/jquery/dist/jquery.js',
    '../../../node_modules/scrolldepth/jquery.scrolldepth.js',
    '../../../node_modules/govuk_frontend_toolkit/javascripts/govuk/analytics/google-analytics-universal-tracker.js',
    '../../../node_modules/govuk_frontend_toolkit/javascripts/govuk/analytics/analytics.js',
    '../../../node_modules/digitalmarketplace-frontend-toolkit/toolkit/javascripts/analytics/_register.js',
    '../../../app/assets/javascripts/analytics/_pageViews.js',
    '../../../app/assets/javascripts/analytics/_events.js',
    '../../../app/assets/javascripts/analytics/_virtualPageViews.js',
    '../../../app/assets/javascripts/analytics/_scrollTracking.js',
    '../../../app/assets/javascripts/analytics/_init.js'
  ],
  test : [
    '../unit/AnalyticsSpec.js'
  ]
};

if (typeof exports !== 'undefined') {
  exports.manifest = manifest;
}
