(function(root) {
  "use strict";

  root.GOVUK.GDM = root.GOVUK.GDM || {};

  var GoogleTagManager = function (containerID, environmentID, authToken) {
    /* eslint-disable */
(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl+ '&gtm_auth='+authToken+'&gtm_preview='+environmentID+'&gtm_cookies_win=x';f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer',containerID)
    /* eslint-enable */
  }

  root.GOVUK.GDM.analytics.googleTagManager = {
    'register': function (gtmConfig) {
      GOVUK.GDM.tagManager = new GoogleTagManager(gtmConfig['containerID'], gtmConfig['environmentID'], gtmConfig['authToken']);

    }
  }
})(window);
