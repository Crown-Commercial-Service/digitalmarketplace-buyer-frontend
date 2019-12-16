(function(root) {
  "use strict";
  root.GOVUK.GDM.analytics.init = function () {
    this.register();
    this.pageViews.init();
    this.events.init();
    this.buyerSpecificEvents.init();
    this.virtualPageViews.init();
    this.scrollTracking.init();
    this.trackExternalLinks.init();
  }

})(window);
