(function(GOVUK, GDM) {

  GDM.selectionButtons = function() {

    if (!GOVUK.SelectionButtons) return;

    new GOVUK.SelectionButtons('.selection-button input');

    if (!GOVUK.ShowHideContent) return;

    new GOVUK.ShowHideContent().init();

  };

  GOVUK.GDM = GDM;

}).apply(this, [GOVUK||{}, GOVUK.GDM||{}]);
