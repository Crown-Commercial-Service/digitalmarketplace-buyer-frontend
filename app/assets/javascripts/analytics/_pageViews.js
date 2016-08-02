(function (GOVUK) {
  GOVUK.GDM.analytics.pageViews = {
    'init': function () {
      this.setCustomDimensions();
      GOVUK.analytics.trackPageview();
    },

    'setCustomDimensions': function() {
      var search = GOVUK.GDM.analytics.location.search(),
          filterGroupDimension = [],
          numberOfOpportunites,
          dimensions,
          pairs,
          pair,
          i,
          j;

      // check that we're on the catalogue page for opportunites
      if (GOVUK.GDM.analytics.location.pathname() === "/digital-outcomes-and-specialists/opportunities") {

        // if it does, we want to send the current number of opportunites back to GA
        numberOfOpportunites = $('.search-summary-count').text();
        GOVUK.analytics.setDimension(21, numberOfOpportunites);

        if (search !== '') {
          // clear the ? prefix
          search = search.split('?')[1];
          pairs = search.split('&');

          dimensions = [
            {
              dimensionId: 23,
              paramType:  'lot',
              paramArray:  [],
            },
            {
              dimensionId: 24,
              paramType:  'status',
              paramArray:  [],
            },
          ]

          j = dimensions.length; while (j--) {
            setFilterDimension(pairs, dimensions[j]);

            // Build array with the names of selected filter group(s) (ie, 'status', 'lot')
            if (dimensions[j]['paramArray'].length) {
              filterGroupDimension.push(dimensions[j]['paramType']);
            }
          }

          if (filterGroupDimension.length) {
            filterGroupDimension.sort();
            GOVUK.analytics.setDimension(22, filterGroupDimension.join('|'));
          }

          function setFilterDimension(pairs, dimension) {
            // If the pairs relate to the given dimension, add their values to the dimension's paramArray
            i = pairs.length;
            while (i--) {
              pair = pairs[i].split('=');

              if (pair[0] === dimension['paramType']) {
                dimension['paramArray'].push(pair[1]);
              }
            }

            // Format paramArray to an ordered list for Google Analytics and set dimension
            if (dimension['paramArray'].length) {
              dimension['paramArray'].sort();
              GOVUK.analytics.setDimension(dimension['dimensionId'], dimension['paramArray'].join('|'));
            }
          }
        }
      }
    }
  };
})(window.GOVUK);
