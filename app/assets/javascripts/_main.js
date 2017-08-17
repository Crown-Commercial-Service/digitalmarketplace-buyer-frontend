$(document).ready(function() {
  jQuery('.scroll-to-top').click(function(e){
    e.preventDefault();
    jQuery('html, body').animate({scrollTop : 0},800);
    return false;
  });
});