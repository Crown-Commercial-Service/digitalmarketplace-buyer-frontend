$(document).ready(function () {
    var radio = $('input[name=approachSelector]');
    if (radio.length > 0) {
        var optional = $('span[class=question-optional]');
        optional.hide();
        function showHideFields() {
            var trainingApproachOwn = $('#trainingApproachOwn');
            var radioVal = $('input[name=approachSelector]:checked').val();
            if (radioVal == 'open') {
                trainingApproachOwn.hide();
            }
            else if (radioVal == 'ownPreference') {
                trainingApproachOwn.show();
            }
            else {
                trainingApproachOwn.hide();
            }
        }

        showHideFields();
        radio.change(function () {
            showHideFields();
        });
    }
});