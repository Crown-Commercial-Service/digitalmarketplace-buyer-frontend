(function(root) {
  "use strict";

  root.GOVUK.GDM.analytics.init = function () {
    this.register();
    this.pageViews.init();
  };
})(window);
