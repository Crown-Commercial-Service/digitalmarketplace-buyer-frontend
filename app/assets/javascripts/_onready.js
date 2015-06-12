(function (root) {

  var GOVUK = root.GOVUK || {};

  $('details').details();
  if (!$.fn.details.support) {
    $('html').addClass('no-details');
  }

})(window);
