(function (GOVUK) {
  GOVUK.GDM.analytics.pageViews = {
    'init': function () {
      this.setCustomDimensions();
      GOVUK.analytics.trackPageview();
    },

    'setCustomDimensions': function() {
      var search = GOVUK.GDM.analytics.location.search(),
          categoryParams = [],
          statusParams = [],
          numberOfOpportunites,
          dimensions,
          pairs,
          pair,
          i,
          j;

      // check that we're on the catalogue page for opportunites
      if(GOVUK.GDM.analytics.location.pathname() === "/digital-outcomes-and-specialists/opportunities") {

        // if it does, we want to send the current number of opportunites back to GA
        numberOfOpportunites = $('.search-summary-count').text();
        GOVUK.analytics.setDimension(21, numberOfOpportunites);

        if(search !== '') {
          // clear the ? prefix
          search = search.split('?')[1];
          pairs = search.split('&');

          dimensions = [
            {
              dimensionId: 23,
              paramType:  'lot',
              paramArray:  categoryParams,
            },
            {
              dimensionId: 24,
              paramType:  'status',
              paramArray:  statusParams,
            },
          ]

          // Using the pairs from the query string, assign them to the correct
          // dimension
          j = dimensions.length; while(j--) {
            setFilterDimension(pairs, dimensions[j]);
          }

          function setFilterDimension(pairs, dimension) {
            i = pairs.length;
            while(i--) {
              pair = pairs[i].split('=');

              if (pair[0] === dimension['paramType']) {
                dimension['paramArray'].push(pair[1]);
              }
            }
            if (dimension['paramArray'].length > 0) {
              dimension['paramArray'].sort();
              GOVUK.analytics.setDimension(dimension['dimensionId'], dimension['paramArray'].join('|'));
            }
          }
        }
      }
    }
  };
})(window.GOVUK);
