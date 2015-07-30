(function() {
  "use strict";
  GOVUK.Analytics.load();
  var cookieDomain = (document.domain === 'www.digitalmarketplace.service.gov.uk') ? '.digitalmarketplace.service.gov.uk' : document.domain;
  var property = (document.domain === 'www.digitalmarketplace.service.gov.uk') ? 'UA-49258698-1' : 'UA-49258698-3';

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
  DMGoogleAnalyticsUniversalTracker.prototype = GOVUK.GoogleAnalyticsUniversalTracker.prototype;
  GOVUK.GoogleAnalyticsUniversalTracker = DMGoogleAnalyticsUniversalTracker;
  GOVUK.analytics = new GOVUK.Analytics({
    universalId: property,
    cookieDomain: cookieDomain
  });
  GOVUK.analytics.trackPageview();
  GOVUK.analytics.addLinkedTrackerDomain(property, 'link', 'digitalservicesstore.service.gov.uk');
})();
