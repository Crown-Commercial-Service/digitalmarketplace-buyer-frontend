var isInBrowser = true;
if (typeof window == 'undefined') {
  var window,
      mock_dom = require('../support/mock_dom.js'),
      isInBrowser = false;
}

describe("GOVUK.Analytics", function () {
  var analytics;

  beforeEach(function(done) {
    var setUp = function () {
      window.ga = function() {};
      spyOn(window, 'ga');
      analytics = new window.GOVUK.Analytics({
        universalId: 'universal-id',
        cookieDomain: 'www.digitalmarketplace.service.gov.uk'
      });
    }

    if (isInBrowser) {
      setUp();
      done();
    } else {
      mock_dom.onReady(function (jsdomWindow) {
        window = jsdomWindow;
        setUp();
        done();
      });
    }
  });

  describe('when created', function() {
    var universalSetupArguments;

    beforeEach(function() {
      universalSetupArguments = window.ga.calls.allArgs();
    });

    it('configures a universal tracker', function() {
      expect(universalSetupArguments[0]).toEqual(['create', 'universal-id', {
        'cookieDomain': 'www.digitalmarketplace.service.gov.uk',
        'allowLinker': true
      }]);
    });
  })
});
