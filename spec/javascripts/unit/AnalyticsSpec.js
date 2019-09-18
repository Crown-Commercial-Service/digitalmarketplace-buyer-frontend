describe("GOVUK.Analytics", function () {
  var analytics,
      sortCalls;

  SortCallsToGaByMethod = function (calls) {
    var gaMethodCalls = {},
        callNum = calls.length;

    while (callNum--) {
      var method = calls[callNum].args.shift(),
          args = calls[callNum].args;

      if (gaMethodCalls.hasOwnProperty(method)) {
        gaMethodCalls[method].push(args);
      } else {
        gaMethodCalls[method] = [args];
      }
    }
    this._calls = gaMethodCalls;
  };
  SortCallsToGaByMethod.prototype.callsTo = function (method) {
    if (this._calls.hasOwnProperty(method)) {
      return this._calls[method];
    }
    return [];
  };

  beforeEach(function () {
    window.ga = function() {};
    spyOn(window, 'ga');
  });

  describe('when initialised', function () {

    it('should initialise pageviews, events, virtual pageviews, track external links and scroll tracking', function () {
      spyOn(window.GOVUK.GDM.analytics, 'register');
      spyOn(window.GOVUK.GDM.analytics.pageViews, 'init');
      spyOn(window.GOVUK.GDM.analytics.events, 'init');
      spyOn(window.GOVUK.GDM.analytics.scrollTracking, 'init');
      spyOn(window.GOVUK.GDM.analytics.trackExternalLinks, 'init');
      spyOn(window.GOVUK.GDM.analytics.buyerSpecificEvents, 'init');

      window.GOVUK.GDM.analytics.init();

      expect(window.GOVUK.GDM.analytics.register).toHaveBeenCalled();
      expect(window.GOVUK.GDM.analytics.pageViews.init).toHaveBeenCalled();
      expect(window.GOVUK.GDM.analytics.events.init).toHaveBeenCalled();
      expect(window.GOVUK.GDM.analytics.scrollTracking.init).toHaveBeenCalled();
      expect(window.GOVUK.GDM.analytics.trackExternalLinks.init).toHaveBeenCalled();
      expect(window.GOVUK.GDM.analytics.buyerSpecificEvents.init).toHaveBeenCalled();
    });
  });

  describe('when registered', function() {
    var universalSetupArguments;

    beforeEach(function() {
      GOVUK.GDM.analytics.init();
      universalSetupArguments = window.ga.calls.allArgs();
    });

    it('configures a universal tracker', function() {
      expect(universalSetupArguments[0]).toEqual(['create', 'UA-49258698-1', {
        'cookieDomain': document.domain
      }]);
      expect(universalSetupArguments[9]).toEqual(['send', 'pageview']);
    });
    it('configures a cross domain tracker', function() {
      expect(universalSetupArguments[2]).toEqual(['create', 'UA-145652997-1', 'auto', {
        'name': 'govuk_shared'
      }]);
      expect(universalSetupArguments[3]).toEqual(['require', 'linker']);
      expect(universalSetupArguments[4]).toEqual(['govuk_shared.require', 'linker']);
      expect(universalSetupArguments[5]).toEqual(['linker:autoLink', [ 'www.gov.uk' ]]);
      expect(universalSetupArguments[6]).toEqual(['govuk_shared.linker:autoLink', [ 'www.gov.uk' ]]);
      expect(universalSetupArguments[7]).toEqual(['govuk_shared.set', 'anonymizeIp', true ]);
      expect(universalSetupArguments[8]).toEqual(['govuk_shared.send', 'pageview']);
    });
  });

  describe('link tracking', function () {
    var mockLink,
        assetHost = 'https://assets.digitalmarketplace.service.gov.uk';

    beforeEach(function () {
      mockLink = document.createElement('a');
      window.ga.calls.reset();
    });

    it('sends the right event when an outcomes supplier responses download link is clicked', function() {
      spyOn(GOVUK.GDM.analytics.location, "pathname")
        .and
        .returnValue('/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1/responses');

      $(mockLink).append('<span class="document-icon">CSV</span><span> document:</span></span>');

      mockLink.appendChild(document.createTextNode('Download supplier responses to ‘Brief 1’'));
      mockLink.href = assetHost + '/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1/responses/download';
      GOVUK.GDM.analytics.buyerSpecificEvents.supplierListDownload({ 'target': mockLink });
      expect(window.ga.calls.first().args).toEqual(['send', {
        'hitType': 'event',
        'eventCategory': 'download',
        'eventAction': 'csv',
        'eventLabel': 'supplier response list | outcomes | 1',
        'transport': 'beacon'
      }]);
    });

    it('sends the right event when a digital specialists supplier responses download link is clicked', function() {
      spyOn(GOVUK.GDM.analytics.location, "pathname")
        .and
        .returnValue('/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1/responses');

      $(mockLink).append('<span class="document-icon">CSV</span><span> document:</span></span>');

      mockLink.appendChild(document.createTextNode('Download supplier responses to ‘Brief 1’'));
      mockLink.href = assetHost + '/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1/responses/download';
      GOVUK.GDM.analytics.buyerSpecificEvents.supplierListDownload({ 'target': mockLink });
      expect(window.ga.calls.first().args).toEqual(['send', {
        'hitType': 'event',
        'eventCategory': 'download',
        'eventAction': 'csv',
        'eventLabel': 'supplier response list | specialists | 1',
        'transport': 'beacon'
      }]);
    });

    it('sends an event requested via html attributes on example of Oportunity Data download', function() {
      $(document.body).append('<a id="opportunity-data" data-analytics="trackEvent" data-analytics-category="opportunity-data-csv" data-analytics-action="download CSV" data-analytics-label="Opportunity Data CSV" href="https://assets.digitalmarketplace.service.gov.uk/digital-outcomes-and-specialists-2/communications/data/opportunity-data.csv">Download data</a>');
      GOVUK.GDM.analytics.events.init();
      $('#opportunity-data').click();
      expect(window.ga.calls.first().args).toEqual(['send', {
        'hitType': 'event',
        'eventCategory': "opportunity-data-csv",
        'eventAction': "download CSV",
        'eventLabel': "Opportunity Data CSV",
        'transport': 'beacon'
      }]);
    });

    it('sends the right event when a list of user research labs download link is clicked', function() {
      spyOn(GOVUK.GDM.analytics.location, "pathname")
        .and
        .returnValue('/buyers/frameworks/digital-outcomes-and-specialists/requirements/user-research-studios');

      $(mockLink).append('<span class="document-icon">CSV</span><span> document:</span></span>');
      mockLink.appendChild(document.createTextNode('List of labs'));
      mockLink.href = assetHost + '/digital-outcomes-and-specialists/communications/catalogues/user-research-studios.csv';
      GOVUK.GDM.analytics.buyerSpecificEvents.supplierListDownload({ 'target': mockLink });
      expect(window.ga.calls.first().args).toEqual(['send', {
        'hitType': 'event',
        'eventCategory': 'download',
        'eventAction': 'csv',
        'eventLabel': 'list of user research labs',
        'transport': 'beacon'
      }]);
    });

    it('sends the right event when a list of user research participants download link is clicked', function() {
      spyOn(GOVUK.GDM.analytics.location, "pathname")
        .and
        .returnValue('/buyers/frameworks/digital-outcomes-and-specialists/requirements/user-research-participants');

      mockLink.appendChild(document.createTextNode('Download list of suppliers.'));
      mockLink.href = assetHost + '/digital-outcomes-and-specialists/communications/catalogues/user-research-participants-suppliers.csv';
      GOVUK.GDM.analytics.buyerSpecificEvents.supplierListDownload({ 'target': mockLink });
      expect(window.ga.calls.first().args).toEqual(['send', {
        'hitType': 'event',
        'eventCategory': 'download',
        'eventAction': 'csv',
        'eventLabel': 'list of user research participant suppliers',
        'transport': 'beacon'
      }]);
    });

    it('sends the right event when a list of suppliers for digital specialists download link is clicked', function() {
      spyOn(GOVUK.GDM.analytics.location, "pathname")
        .and
        .returnValue('/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists');

      mockLink.appendChild(document.createTextNode('Download list of suppliers.'));
      mockLink.href = assetHost + '/digital-outcomes-and-specialists/communications/catalogues/digital-specialists-suppliers.csv';
      GOVUK.GDM.analytics.buyerSpecificEvents.supplierListDownload({ 'target': mockLink });
      expect(window.ga.calls.first().args).toEqual(['send', {
        'hitType': 'event',
        'eventCategory': 'download',
        'eventAction': 'csv',
        'eventLabel': 'list of specialists suppliers',
        'transport': 'beacon'
      }]);
    });

    it('sends the right event when a list of suppliers for digital outcomes download link is clicked', function() {
      spyOn(GOVUK.GDM.analytics.location, "pathname")
        .and
        .returnValue('/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes');

      mockLink.appendChild(document.createTextNode('Download list of suppliers.'));
      mockLink.href = assetHost + '/digital-outcomes-and-specialists/communications/catalogues/digital-outcomes-suppliers.csv';
      GOVUK.GDM.analytics.buyerSpecificEvents.supplierListDownload({ 'target': mockLink });
      expect(window.ga.calls.first().args).toEqual(['send', {
        'hitType': 'event',
        'eventCategory': 'download',
        'eventAction': 'csv',
        'eventLabel': 'list of outcomes suppliers',
        'transport': 'beacon'
      }]);
    });
  });

  describe("Virtual Page Views", function () {
    var $analyticsString;
    var filterTemplate = 
        '<form id="js-dm-live-search-form">' + 
            '<div class="dm-filters">' +
              '<div class="options-container" id="example-filters-group" data-framework="g-cloud" data-current-lot="test-lot">' +
                '<div class="js-auto-height-inner">' +
                  '<label for="filter-option-1">' +
                    '<input name="filter-option-1" value="filter-option-1-value" id="filter-option-1" type="checkbox" aria-controls="">' +
                    'filter-option-1-label' +
                  '</label>' +
                '</div>' +
              '</div>' +
            '</div>' +
          '</form>';

    afterEach(function () {
      $analyticsString.remove();
    });

    it("Should not call google analytics without a url", function () {
      $analyticsString = $("<div data-analytics='trackPageView'/>");
      $(document.body).append($analyticsString);
      window.GOVUK.GDM.analytics.virtualPageViews.init();
      expect(window.ga.calls.any()).toEqual(false);
    });

    it("Should call google analytics if url exists", function () {
      $analyticsString = $("<div data-analytics='trackPageView' data-url='http://example.com'/>");
      $(document.body).append($analyticsString);
      window.GOVUK.GDM.analytics.virtualPageViews.init();
      expect(window.ga.calls.first().args).toEqual([ 'send', 'pageview', { page: 'http://example.com/vpv' } ]);
      expect(window.ga.calls.count()).toEqual(1);
    });


    it("Should add '/vpv/' to url before question mark", function () {
      $analyticsString = $('<div data-analytics="trackPageView" data-url="http:/testing.co.uk/testrubbs?sweet"/>');
      $(document.body).append($analyticsString);
      window.GOVUK.GDM.analytics.virtualPageViews.init();
      expect(window.ga.calls.first().args[2]).toEqual({page: "http:/testing.co.uk/testrubbs/vpv?sweet"});
    });

    it("Should add '/vpv/' to url at the end if no question mark", function () {
      $analyticsString = $("<div data-analytics='trackPageView' data-url='http://example.com'/>");
      $(document.body).append($analyticsString);
      window.GOVUK.GDM.analytics.virtualPageViews.init();
      expect(window.ga.calls.first().args[2]).toEqual({page: "http://example.com/vpv"});
    });

    it("Should trigger virtual page view on filter selection", function () {
      $analyticsString = $( filterTemplate );
      $(document.body).append($analyticsString);
      window.GOVUK.GDM.analytics.virtualPageViews.init();
      $('#filter-option-1').click();
      expect(window.ga.calls.first().args[2]).toEqual({
        page: "/g-cloud/test-lot/filters/example-filters-group/filter-option-1/filter-option-1-value/vpv", 
        title: "Filter - g-cloud - test-lot - example-filters-group - filter-option-1 - filter-option-1-value"
      });
    });

    it("Should not trigger virtual page view if a user is removing a filter", function () {
      $analyticsString = $( filterTemplate );
      $analyticsString.find('#filter-option-1').attr('checked', 'checked');
      $(document.body).append($analyticsString);
      window.GOVUK.GDM.analytics.virtualPageViews.init();
      $('#filter-option-1').click();
      expect(window.ga.calls.first()).not.toBeDefined();
    });
  });

  describe("Opportunities search page", function() {
    var $counter = $('<span class="search-summary-count">32</span>');

    beforeEach(function () {
      $(document.body).append($counter);

      spyOn(GOVUK.GDM.analytics.location, "pathname")
        .and
        .returnValue('/digital-outcomes-and-specialists/opportunities');
    });

    afterEach(function () {
      $counter.remove();
    });

    setupQueryString = function (query_string) {
      spyOn(GOVUK.GDM.analytics.location, "search")
        .and
        .returnValue(query_string);

      window.GOVUK.GDM.analytics.pageViews.init();
    };

    it('should send the number of results as a custom dimension', function() {
      window.GOVUK.GDM.analytics.pageViews.init();

      expect(window.ga.calls.first().args).toEqual(['set', 'dimension21', '32']);
    });

    it('should send the category filters as a custom dimension if only one', function() {
      setupQueryString('?lot=digital-outcomes');

      expect(window.ga.calls.all()[1].args).toEqual(['set', 'dimension23', 'digital-outcomes']);
    });

    it('should send the category filters as a custom dimension if multiple', function() {
      setupQueryString('?lot=digital-outcomes&lot=digital-specialists');

      expect(window.ga.calls.all()[1].args).toEqual(['set', 'dimension23', 'digital-outcomes|digital-specialists']);
    });

    it('should send the category filters as a custom dimension if multiple and in wrong order', function() {
      setupQueryString('?lot=digital-specialists&lot=digital-outcomes');

      expect(window.ga.calls.all()[1].args).toEqual(['set', 'dimension23', 'digital-outcomes|digital-specialists']);
    });

    it('should send the status filters as a custom dimension if only one', function() {
      setupQueryString('?status=closed');

      expect(window.ga.calls.all()[1].args).toEqual(['set', 'dimension24', 'closed']);
    });

    it('should send the status filters as a custom dimension if multiple', function() {
      setupQueryString('?status=closed&status=live');

      expect(window.ga.calls.all()[1].args).toEqual(['set', 'dimension24', 'closed|live']);
    });

    it('should send the status filters as a custom dimension if multiple and in wrong order', function() {
      setupQueryString('?status=live&status=closed');

      expect(window.ga.calls.all()[1].args).toEqual(['set', 'dimension24', 'closed|live']);
    });

    it('should send the filter groups as a custom dimension if one', function() {
      setupQueryString('?status=closed');

      expect(window.ga.calls.all()[2].args).toEqual(['set', 'dimension22', 'status']);
    });

    it('should send the filter groups as a custom dimension if multiple', function() {
      setupQueryString('?status=closed&lot=digital-specialists');

      expect(window.ga.calls.all()[3].args).toEqual(['set', 'dimension22', 'lot|status']);
    });

    it('should send the filter groups as a custom dimension if multiple and wrong order', function() {
      setupQueryString('?lot=digital-specialists&status=closed');

      expect(window.ga.calls.all()[3].args).toEqual(['set', 'dimension22', 'lot|status']);
    });

    it('should send the correct custom dimension if all filters are used', function() {
      setupQueryString('?lot=digital-specialists&status=closed&lot=digital-outcomes&status=live&lot=user-research-participants');

      expect(window.ga.calls.first().args).toEqual(['set', 'dimension21', '32']);
      expect(window.ga.calls.all()[1].args).toEqual(['set', 'dimension24', 'closed|live']);
      expect(window.ga.calls.all()[2].args).toEqual(['set', 'dimension23', 'digital-outcomes|digital-specialists|user-research-participants']);
      expect(window.ga.calls.all()[3].args).toEqual(['set', 'dimension22', 'lot|status']);
    });

  });

  describe("Opportunity page", function() {
    var lotData = $('<span data-lot="test-lot"></span>');

    beforeEach(function () {
      $(document.body).append(lotData);
    });

    afterEach(function () {
      lotData.remove();
    });

    it('should send the lot as a custom dimension for any DOS lot', function() {
      spyOn(GOVUK.GDM.analytics.location, "pathname")
        .and
        .returnValue('/digital-outcomes-and-specialists-3/opportunities/100');
      window.GOVUK.GDM.analytics.pageViews.init();
      expect(window.ga.calls.all().map(function (i) {return i.args})).toContain(['set', 'dimension26', 'test-lot']);
    });

    it('should not send the lot as a custom dimension for any non DOS lot', function() {
      spyOn(GOVUK.GDM.analytics.location, "pathname")
        .and
        .returnValue('/not-digital-outcomes-and-specialists/opportunities/100');
      window.GOVUK.GDM.analytics.pageViews.init();
      expect(window.ga.calls.all().map(function (i) {return i.args})).not.toContain(['set', 'dimension26', 'test-lot']);
    });
  });
});
