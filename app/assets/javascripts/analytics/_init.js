(function(root) {
  "use strict";

  // cookie_policy is currently set to opt-in analytics by default
  // If no policy set or policy set to opt-out, don't initialise analytics
  var currentConsentCookie = window.GOVUK.GDM.getCookie('cookie_policy')
  var currentConsentCookieJSON = JSON.parse(currentConsentCookie)
  if (currentConsentCookieJSON && currentConsentCookieJSON['usage']) {
      root.GOVUK.GDM.analytics.init = function () {
        this.register();
        this.pageViews.init();
        this.events.init();
        this.buyerSpecificEvents.init();
        this.virtualPageViews.init();
        this.scrollTracking.init();
        this.trackExternalLinks.init();
      }
  }

})(window);
