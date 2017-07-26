(function (GOVUK) {
  "use strict";

  function ScrollTracking() {
    this.trackedElements = [];
  }

  ScrollTracking.init = function(){};

  ScrollTracking.prototype.init = function () {

    var _this = this;

    $('.scroll-tracking').each(function () {
      _this.trackedElements.push('#' + $(this).attr('id'));
    });

    jQuery.scrollDepth({
      elements: this.trackedElements,
      percentage: false, // Percentage events are fired at the 25%, 50%, 75%, and 100% scrolling points
      userTiming: true, // amount of time (ms) between the page load and the scroll point
      pixelDepth: false, // scroll distance in pixels, rounded down to the nearest 250px increment
    });
  };

  GOVUK = GOVUK || {};
  GOVUK.GDM = GOVUK.GDM || {};
  GOVUK.GDM.analytics = GOVUK.GDM.analytics || {};
  GOVUK.GDM.analytics.scrollTracking = new ScrollTracking();

})(window.GOVUK);
