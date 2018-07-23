$(document).ready(function () {
    var radio = $('input[name^=lds][name$=ProposalOrLds]');            
    if (radio.length > 0) {
        var optional = $('span[class=question-optional]');
        optional.hide();
        function showHideFields() {
            var units = $('fieldset[id^=lds][id$=Units]');
            var trainingNeeds = $('div[id^=lds][id$=TrainingNeeds]');
            var radioVal = $('input[name^=lds][name$=ProposalOrLds]:checked').val();
            if (radioVal == 'sellerProposal') {
                units.hide();
                trainingNeeds.hide();
            }
            else if (radioVal == 'ldsUnits') {
                units.show();
                trainingNeeds.hide();
            }
            else if (radioVal == 'specify') {
                units.hide();
                trainingNeeds.show();
            }
            else {
                units.hide();
                trainingNeeds.hide();
            }
        }

        showHideFields();
        radio.change(function () {
            showHideFields();
        });
    }
});