(function() {
  "use strict";
  // Rewritten GOVUK.Analytics
  var DMAnalytics = function(config) {
    this.trackers = [];
    if (typeof config.universalId != 'undefined') {
      if (typeof config.receiveCrossDomainTracking !== 'undefined') {
        this.trackers.push(new GOVUK.GoogleAnalyticsUniversalTracker(config.universalId, config.cookieDomain, true));
      } else {
        this.trackers.push(new GOVUK.GoogleAnalyticsUniversalTracker(config.universalId, config.cookieDomain));
      }
    }
  };
  DMAnalytics.load = GOVUK.Analytics.load;
  DMAnalytics.prototype = GOVUK.Analytics.prototype;
  GOVUK.Analytics = DMAnalytics;
  // wrapper function for calls to window.ga, used by all Google Analytics trackers
  function sendToGa() {
    if (typeof window.ga === "function") {
      ga.apply(window, arguments);
    }
  };
  // Rewritten universal tracker to allow setting of the autoLinker property
  var DMGoogleAnalyticsUniversalTracker = function(id, cookieDomain, allowLinker) {
    this.defaultTrackerIsAutoLinked = false;
    configureProfile.apply(this, arguments);
    anonymizeIp();

    function configureProfile(id, cookieDomain, allowLinker) {
      var gaOptions = { 'cookieDomain' : cookieDomain };

      if (typeof allowLinker !== 'undefined') {
        gaOptions.allowLinker = allowLinker;
      }
      sendToGa('create', id, gaOptions);
    }

    function anonymizeIp() {
      // https://developers.google.com/analytics/devguides/collection/analyticsjs/advanced#anonymizeip
      sendToGa('set', 'anonymizeIp', true);
    }
  };
  DMGoogleAnalyticsUniversalTracker.load = GOVUK.GoogleAnalyticsUniversalTracker.load;
  DMGoogleAnalyticsUniversalTracker.prototype = GOVUK.GoogleAnalyticsUniversalTracker.prototype;
  // Rewritten add linked tracker domain method too allow use of an existing tracker
  DMGoogleAnalyticsUniversalTracker.prototype.addLinkedTrackerDomain = function(domain, trackerOptions) {
    // if a new tracker is required, create it here
    if (typeof trackerOptions !== 'undefined') {
      sendToGa('create',
               trackerOptions.trackerId,
               'auto',
               {'name': trackerOptions.name});

      // Load the plugin.
      sendToGa(name + '.require', 'linker');

      // Define which domains to autoLink.
      sendToGa(name + '.linker:autoLink', [domain]);

      sendToGa(name + '.set', 'anonymizeIp', true);
      sendToGa(name + '.send', 'pageview');
    }

    if (!this.defaultTrackerIsAutoLinked) {
      // Load the plugin.
      sendToGa('require', 'linker');

      // Define which domains to autoLink.
      sendToGa('linker:autoLink', [domain]);

      this.defaultTrackerIsAutoLinked = true
    }
  };
  GOVUK.GoogleAnalyticsUniversalTracker = DMGoogleAnalyticsUniversalTracker;
})();
