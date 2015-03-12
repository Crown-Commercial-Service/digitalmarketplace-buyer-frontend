(function (root) {
  var GOVUK = root.GOVUK || {};

  if (GOVUK.CheckboxFilter) {
    var filters = $('.js-openable-filter').map(function(){
      return new GOVUK.CheckboxFilter({el:$(this)});
    });

    if (filters.length > 0 && $('.js-openable-filter').not('.closed').length == 0) {
      filters[0].open();
    }
  }

  $('details').details();
  if (!$.fn.details.support) {
    $('html').addClass('no-details');
  }
})(window);
