$(document).ready(function() {
  $('a.expand-terms').on('click', function (e) {
    e.preventDefault();
    $('.accept-new-terms-content').toggleClass('hidden');
  })
});
