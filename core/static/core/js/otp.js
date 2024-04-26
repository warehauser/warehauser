
$(document).ready(function () {
    // Attach event listeners to OTP input fields
    $('.otp').on('click', function (e) {
        e.preventDefault();
        handleOTPFieldClick($(this));
    });

    $('.otp').on('keyup', function (e) {
        e.preventDefault();
        handleOTPFieldKeyup($(this));
    });

    $('.otp').on('paste', function (e) {
        e.preventDefault();
        handleOTPPaste($(this));
    });
});

function handleOTPFieldClick(inputField) {
    // Check if the input field is empty
    if (!inputField.val()) {
        // Automatically select the first empty input field
        $('.otp').removeClass('selected');
        inputField.addClass('selected');
    } else {
        // Automatically select the text in the non-empty input field
        inputField.select();
    }
}

function handleOTPFieldKeyup(inputField) {
    // Check if the input field is empty
    if (!inputField.val()) {
        // Automatically select the first non-empty input field
        $('.otp').removeClass('selected');
        inputField.addClass('selected');
    }

    // Check if the entered character is [a-z], convert to uppercase, and insert into the field
    let enteredChar = inputField.val().charAt(0);
    if (/^[a-z]$/.test(enteredChar)) {
        inputField.val(enteredChar.toUpperCase());
        inputField.removeClass('selected');
        inputField.next('.otp').addClass('selected').focus();
    } else if (/^[A-Z0-9]$/.test(enteredChar)) {
        inputField.removeClass('selected');
        inputField.next('.otp').addClass('selected').focus().val(enteredChar);
    }
}

function handleOTPPaste(inputField) {
    // Get the text from clipboard
    let clipboardText = e.originalEvent.clipboardData.getData('text/plain');

    // Process the clipboard text
    for (let char of clipboardText) {
        // Check if the character is [a-z], convert to uppercase, and insert into the field
        if (/^[a-z]$/.test(char)) {
            inputField.val(char.toUpperCase());
        } else if (/^[A-Z0-9]$/.test(char)) {
            inputField.val(char);
        }

        // Automatically advance the focus to the next input field
        inputField.removeClass('selected');
        inputField.next('.otp').addClass('selected').focus();
        inputField = inputField.next('.otp');
    }
}
