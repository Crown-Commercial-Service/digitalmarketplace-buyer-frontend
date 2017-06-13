(function(root) {
  "use strict";

  root.GOVUK.GDM.analytics.init = function () {
    this.register();
    this.pageViews.init();
    this.events.init();
    this.virtualPageViews();

    var config = document.getElementById('config');
    var gtmConfig = JSON.parse(config.dataset.googleTagManager);
    this.googleTagManager.register(gtmConfig);

  };
})(window);
