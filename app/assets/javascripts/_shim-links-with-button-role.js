// Javascript shim for accessibility incase we use `role="button"` in our front end code. See GOV.UK front end toolkit
// for further documentation
(function(GOVUK, GDM) {

  GDM.shimLinksWithButtonRole = function() {

    if (!GOVUK.shimLinksWithButtonRole) return;

    GOVUK.shimLinksWithButtonRole.init();

  };

  GOVUK.GDM = GDM;

}).apply(this, [GOVUK||{}, GOVUK.GDM||{}]);
