(function (GOVUK) {
  "use strict";

  var VirtualPageViews = function(){};

  VirtualPageViews.prototype.init = function() {

    var _this = this;

    $('[data-analytics=trackPageView]').each(function(){
      var url = $(this).data('url');
      _this.sendVirtualPageView( url );
    }).bind(this);

    $('#js-dm-live-search-form .dm-filters').on('change', 'input[type=checkbox]', this.filterSelected);

  };

  VirtualPageViews.prototype.sendVirtualPageView = function( url, name ) {

    if ( GOVUK.analytics  && url ) {
      var urlList = url.split("?");
      urlList[0]  = urlList[0] + "/vpv";
      url         = urlList.join("?");
      GOVUK.analytics.trackPageview(url, name);
    }

  };

  VirtualPageViews.prototype.trackFilterAnalytics = function( group, key, value ) {

    var filter_path = '/' + group + '/' + key + '/' + value;
    var url = '/g-cloud/filters' + filter_path;
    this.sendVirtualPageView( url, 'Filter' + filter_path.replace(/[/]/g, " - ") );

  };

  VirtualPageViews.prototype.filterSelected = function(){
    if(this.checked) {
      var group = $(this).closest('.options-container').attr('id');
      var key = $(this).attr('name');
      var value = $(this).attr('value');
      GOVUK.GDM.analytics.virtualPageViews.trackFilterAnalytics(group, key, value);
    }
  };

  GOVUK = GOVUK || {};
  GOVUK.GDM = GOVUK.GDM || {};
  GOVUK.GDM.analytics = GOVUK.GDM.analytics || {};
  GOVUK.GDM.analytics.virtualPageViews = new VirtualPageViews();
  
})(window.GOVUK);
