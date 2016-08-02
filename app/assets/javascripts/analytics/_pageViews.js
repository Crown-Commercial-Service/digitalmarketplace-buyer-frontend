(function (GOVUK) {
  GOVUK.GDM.analytics.pageViews = {
    'init': function () {
      this.setCustomDimensions();
      GOVUK.analytics.trackPageview();
    },

    'setCustomDimensions': function() {
      // check that we're on the catalogue page for opportunites
      if(GOVUK.GDM.analytics.location.pathname() === "/digital-outcomes-and-specialists/opportunities") {

        // if it does, we want to send the current number of opportunites back to GA
        numberOfOpportunites = $('.search-summary-count').text();
        GOVUK.analytics.setDimension(21, numberOfOpportunites);
      }
    }
  };
})(window.GOVUK);
