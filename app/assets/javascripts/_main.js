$(document).ready(function() {
  var offset = 250;

  var duration = 300;

  jQuery(window).scroll(function() {
    if (jQuery(this).scrollTop() > offset) {
      jQuery('.scroll-to-top').fadeIn(duration);
    } else {
      jQuery('.scroll-to-top').fadeOut(duration);
    }
  });

  jQuery('.scroll-to-top').click(function(e){
    e.preventDefault();
    jQuery('html, body').animate({scrollTop : 0},800);
    return false;
  });
});