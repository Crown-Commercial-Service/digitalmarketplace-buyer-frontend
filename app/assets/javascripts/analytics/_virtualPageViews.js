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

  VirtualPageViews.prototype.sendVirtualPageView = function( url, name, dimensions ) {

    if ( !GOVUK.analytics || !url ) return false;

    if ( dimensions )
    {
      for ( var i = 0; i < dimensions.length; i++ )
      {
        var dimension = dimensions[i];
        GOVUK.analytics.setDimension(dimension.id, dimension.label);
      }
    }

    var urlList = url.split("?");
    urlList[0]  = urlList[0] + "/vpv";
    url         = urlList.join("?");
    GOVUK.analytics.trackPageview(url, name);

  };

  VirtualPageViews.prototype.trackFilterAnalytics = function( framework, lot, group, key, value ) {
    var url = '/' + framework + '/' + lot + '/filters' + '/' + group + '/' + key + '/' + value;
    var pageTitle = 'Filter' + url.replace('/filters/', '/').replace(/[/]/g, " - ");
    this.sendVirtualPageView(url, pageTitle);
  };

  VirtualPageViews.prototype.filterSelected = function(){
    if(this.checked) {
      var framework = $(this).closest('.options-container').attr('data-framework');
      framework = framework ? framework : 'no-framework-given';
      var lot = $(this).closest('.options-container').attr('data-current-lot');
      lot = lot ? lot : 'no-lot-selected';
      var group = $(this).closest('.options-container').attr('id');
      var key = $(this).attr('name');
      var value = $(this).attr('value');
      GOVUK.GDM.analytics.virtualPageViews.trackFilterAnalytics(framework, lot, group, key, value);
    }
  };

  GOVUK = GOVUK || {};
  GOVUK.GDM = GOVUK.GDM || {};
  GOVUK.GDM.analytics = GOVUK.GDM.analytics || {};
  GOVUK.GDM.analytics.virtualPageViews = new VirtualPageViews();
  
})(window.GOVUK);
