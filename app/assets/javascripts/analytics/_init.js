(function() {
  "use strict";
  var cookieDomain = (document.domain === 'www.digitalmarketplace.service.gov.uk') ? '.digitalmarketplace.service.gov.uk' : document.domain;
  var property = (document.domain === 'www.digitalmarketplace.service.gov.uk') ? 'UA-49258698-1' : 'UA-49258698-3';

  GOVUK.Analytics.load();
  GOVUK.analytics = new GOVUK.Analytics({
    universalId: property,
    cookieDomain: cookieDomain,
    receiveCrossDomainTracking: true
  });
  GOVUK.analytics.trackPageview();
  GOVUK.analytics.addLinkedTrackerDomain('digitalservicesstore.service.gov.uk');
})();
