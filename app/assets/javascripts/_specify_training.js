$(document).ready(function () {
    var radio = $('input[name=specifyTrainingProposalOrDefine]');
    if (radio.length > 0) {
        function showHideFields() {
            var specifyTrainingCover = $('#specifyTrainingCover');
            var specifyTrainingType = $('#specifyTrainingType');
            var radioVal = $('input[name=specifyTrainingProposalOrDefine]:checked').val();
            if (radioVal == 'sellerProposal') {
                specifyTrainingCover.hide();
                specifyTrainingType.show();
            }
            else if (radioVal == 'define') {
                specifyTrainingCover.show();
                specifyTrainingType.show();
            }
            else {
                specifyTrainingCover.hide();
                specifyTrainingType.hide();
            }
        }

        showHideFields();
        radio.change(function () {
            showHideFields();
        });
    }
});