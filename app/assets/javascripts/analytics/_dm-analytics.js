(function() {
  "use strict";
  // wrapper function for calls to window.ga, used by all Google Analytics trackers
  function sendToGa() {
    if (typeof window.ga === "function") {
      ga.apply(window, arguments);
    }
  }
  // Rewritten universal tracker to allow setting of the autoLinker property
  var DMGoogleAnalyticsUniversalTracker = function(id, cookieDomain) {
    configureProfile(id, cookieDomain);
    anonymizeIp();

    function configureProfile(id, cookieDomain) {
      sendToGa('create', id, {'cookieDomain': cookieDomain, 'allowLinker': true });
    }

    function anonymizeIp() {
      // https://developers.google.com/analytics/devguides/collection/analyticsjs/advanced#anonymizeip
      sendToGa('set', 'anonymizeIp', true);
    }
  };
  DMGoogleAnalyticsUniversalTracker.load = GOVUK.GoogleAnalyticsUniversalTracker.load;
  DMGoogleAnalyticsUniversalTracker.prototype = GOVUK.GoogleAnalyticsUniversalTracker.prototype;
  GOVUK.GoogleAnalyticsUniversalTracker = DMGoogleAnalyticsUniversalTracker;
})();
