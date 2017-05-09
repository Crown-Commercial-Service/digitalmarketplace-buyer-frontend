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

    it('should initialise pageviews, events and virtual pageviews', function () {
      spyOn(window.GOVUK.GDM.analytics, 'register');
      spyOn(window.GOVUK.GDM.analytics.pageViews, 'init');
      spyOn(window.GOVUK.GDM.analytics.events, 'init');

      window.GOVUK.GDM.analytics.init();

      expect(window.GOVUK.GDM.analytics.register).toHaveBeenCalled();
      expect(window.GOVUK.GDM.analytics.pageViews.init).toHaveBeenCalled();
      expect(window.GOVUK.GDM.analytics.events.init).toHaveBeenCalled();
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
      GOVUK.GDM.analytics.events.supplierListDownload({ 'target': mockLink });
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
      GOVUK.GDM.analytics.events.supplierListDownload({ 'target': mockLink });
      expect(window.ga.calls.first().args).toEqual(['send', {
        'hitType': 'event',
        'eventCategory': 'download',
        'eventAction': 'csv',
        'eventLabel': 'supplier response list | specialists | 1',
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
      GOVUK.GDM.analytics.events.supplierListDownload({ 'target': mockLink });
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
      GOVUK.GDM.analytics.events.supplierListDownload({ 'target': mockLink });
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
      GOVUK.GDM.analytics.events.supplierListDownload({ 'target': mockLink });
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
      GOVUK.GDM.analytics.events.supplierListDownload({ 'target': mockLink });
      expect(window.ga.calls.first().args).toEqual(['send', {
        'hitType': 'event',
        'eventCategory': 'download',
        'eventAction': 'csv',
        'eventLabel': 'list of outcomes suppliers',
        'transport': 'beacon'
      }]);
    });
  });

  describe("Virtual Page DashboardBriefs", function () {
    var $analyticsString;

    afterEach(function () {
      $analyticsString.remove();
    });

    it("Should not call google analytics without a url", function () {
      $analyticsString = $("<div data-analytics='trackPageView'/>");
      $(document.body).append($analyticsString);
      window.GOVUK.GDM.analytics.virtualPageViews();
      expect(window.ga.calls.any()).toEqual(false);
    });

    it("Should call google analytics if url exists", function () {
      $analyticsString = $("<div data-analytics='trackPageView' data-url='http://example.com'/>");
      $(document.body).append($analyticsString);
      window.GOVUK.GDM.analytics.virtualPageViews();
      expect(window.ga.calls.first().args).toEqual([ 'send', 'pageview', { page: 'http://example.com' } ]);
      expect(window.ga.calls.count()).toEqual(1);
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
});
