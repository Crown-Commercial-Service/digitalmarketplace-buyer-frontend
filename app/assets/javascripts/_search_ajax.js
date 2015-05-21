(function (root) {

  var GOVUK = root.GOVUK || {},
      resultsTemplate = Hogan.compile(
        '{{#services}}' +
          '<div class="search-result">' +
            '<h2 class="search-result-title">' +
              '<a href="#">{{serviceName}}</a>' +
            '</h2>' +
            '<p class="search-result-supplier">' +
              '{{supplierName}}' +
            '</p>' +
            '<p class="search-result-excerpt">' +
              '{{{serviceSummary}}}' +
            '</p>' +
            '<ul class="search-result-metadata">' +
              '<li class="search-result-metadata-item" aria-label="Framework">' +
                '{{frameworkName}}' +
              '</li>' +
              '<li class="search-result-metadata-item"  aria-label="Lot">' +
                '{{lot}}' +
              '</li>' +
            '</ul>' +
          '</div>' +
        '{{/services}}'
      ),
      getResults = function() {

        requestCounter++;

        var counterAtTimeOfRequest = requestCounter;

        $.ajax(
          '/search?' + $("form").serialize(),
          {
            success: function(data) {

              if (requestCounter > counterAtTimeOfRequest) return;

              $("#search-results").html(resultsTemplate.render(data));
              $(".search-summary").html(data.summary);

            }
          }
        );

      },
      requestCounter = 0;

  $(":checkbox").change(getResults);
  $(".filter-field-text").on("keyup", getResults);

})(window);
