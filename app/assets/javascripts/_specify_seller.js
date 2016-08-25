$(document).ready(function() {
    var sellerSelector = $('input[name=sellerSelector]');
    function showHideEmailFields(){
        var sellerEmail = $('#sellerEmail');
        var sellerEmailList = $('#sellerEmailList');
        var radioVal = $('input[name=sellerSelector]:checked').val();
        if(radioVal == 'allSellers'){
            sellerEmail.hide();
            sellerEmailList.hide();
        }
        else if(radioVal == 'someSellers'){
            sellerEmail.hide();
            sellerEmailList.show();
        }
        else if(radioVal == 'oneSeller'){
            sellerEmail.show();
            sellerEmailList.hide();
        }
        else{
            sellerEmail.hide();
            sellerEmailList.hide();
        }
    }

    if(sellerSelector.length > 0){
        showHideEmailFields();
        sellerSelector.change(function(){
            showHideEmailFields();
        });
    }
});