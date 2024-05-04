/* Copyright 2024 warehauser @ github.com

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. */

// warehauser.js

window.onload = function() {
    const body = document.body;

    let forms = document.querySelectorAll('form');
    forms.forEach(form => {
        init_form(form);
    });
};

forms = {};
function init_form(form) {
    forms[form.id] = {};

    fields = form.querySelectorAll('input:not([type="hidden"]), textarea');
    fields.forEach((field) => {
        if(field.type === 'text' || field.type === 'password' || field.type === 'datetime' || field.type === 'datetime-local' || field.type === 'textarea') {
            if(field.hasAttribute('required')) {
                forms[form.id][field.id] = field.checkValidity();
            } else {
                if(!field.hasAttribute('placeholder')) {
                    field.setAttribute('placeholder', '');
                }
            }
        }
    });

    formHeader = document.getElementById('form-header-' + form.id);
    if(formHeader) {
        formHeader.addEventListener('animationend', () => {
            formHeader.classList.remove('shake-animation');
        });
    }
}

function remove_error(input) {
    input.parentElement.classList.remove('error');
}

let show_hide_timeouts = {}
function show_hide(toggle, id, seconds=0) {
    let input = document.getElementById(id);
    if(input.type === 'password') {
        input.setAttribute('type', 'text');
        toggle.setAttribute('name', 'eye-off-outline');
        input.focus()

        if(seconds > 0) {
            // Automatically reset the input type to password after specified seconds
            show_hide_timeouts[id] = setTimeout(() => {
                input.setAttribute('type', 'password');
                toggle.setAttribute('name', 'eye-outline');
                delete show_hide_timeouts[id];
            }, seconds * 1000); // Convert seconds to milliseconds
        }
    } else {
        if(show_hide_timeouts[id] !== null) {
            clearTimeout(show_hide_timeouts[id]);
            delete show_hide_timeouts[id];
        }
        input.setAttribute('type', 'password');
        toggle.setAttribute('name', 'eye-outline');
        input.focus()
    }
}

function shake_form_header(form) {
    const formHeader = document.getElementById('form-header-' + form.id);
    formHeader.classList.add('shake-animation');
}

function show_logged_in(form)
{
    let header = document.getElementById('form-title-' + form.id);
    if(header){
        header.innerText = 'Logged In';
    }

    let icon = document.getElementById('form-header-icon-' + form.id);
    let lock_icon = document.getElementById('lock-open-icon');

    if(icon && lock_icon) {
        const icon_rect = icon.getBoundingClientRect();
        const lock_rect = lock_icon.getBoundingClientRect();

        let offsetLeft = lock_rect.left - icon_rect.left;
        let offsetTop = lock_rect.top - icon_rect.top;

        document.documentElement.style.setProperty('--target-rect-left', offsetLeft + 'px');
        // document.documentElement.style.setProperty('--target-rect-right', targetElementRect.right + 'px');
        document.documentElement.style.setProperty('--target-rect-top', offsetTop + 'px');
        // document.documentElement.style.setProperty('--target-rect-bottom', targetElementRect.bottom + 'px');

        icon.setAttribute('name', 'lock-open-outline');
        icon.classList.add('icon-login-animation');
        icon.addEventListener('animationend', (event) => {
            lock_icon.style.visibility = 'visible';
            icon.style.visibility = 'hidden';
            icon.classList.remove('icon-login-animation');

            function opacity_listener(event)
            {
                const target = event.target;
                target.classList.remove('opaque');
                target.classList.remove('user-info-animation');
            }

            divider = document.getElementById('session-info-divider');
            divider.addEventListener('animationend', opacity_listener);
            divider.classList.add('user-info-animation');

            let user_info = document.getElementById('user-info');
            user_info.addEventListener('animationend', opacity_listener);
            user_info.classList.add('user-info-animation');
        });
    }
}

function disable_link(link) {
    link.classList.add('disabled-link');
    link.setAttribute('tabindex', -1);
    link.setAttribute('href', 'javascript:void(0);');
    link.addEventListener('click', (event) => {
        event.preventDefault(); // Prevent the default behavior of anchor links
    });
}

async function submit_login_form(form) {
    // disable all submit buttons
    let submitButtons = form.querySelectorAll('button[type="submit"]');
    submitButtons.forEach((button) => {
        button.disabled = true;
    });

    let links = form.querySelectorAll('a');
    links.forEach((link) => {
        disable_link(link)
    });

    formData = new FormData();
    fields = form.querySelectorAll('input, textarea')
    fields.forEach((field) => {
        field.parentElement.classList.remove('error');
        field.disabled = true;

        formData.append(field.name, field.value);
    });

    let response = await fetch(form.action, {
        method: form.method,
        body: formData
    }).then((response) => {
        if(!response.ok) {
            // We are logged in! :-)
            show_logged_in(form);
        } else {
            // We did not log in! :-(
            shake_form_header(form);
            // Enable all submit buttons and fields that where disabled above...
            submitButtons.forEach(button => {
                button.disabled = false;
            });
            fields.forEach(field => {
                field.disabled = false;
            });
        }
    });

    return false;
}

function submit_form(form) {
    return false;
}

function form_display_validity(form)
{
    let submitters = Array.from(form.querySelectorAll('button, input[type="submit"]')); // Get all buttons and submit inputs in the form
    let formValid = forms[form.id];
    let valid = true;
    Object.keys(formValid).forEach((key) => {
        valid = valid && formValid[key];
    });

    // Check if the input is valid
    if (valid) {
        // Handle the case where the input is valid
        // For example, remove the error class from the input's parent element

        // Enable all buttons and submit inputs
        submitters.forEach((button) => {
            button.removeAttribute('disabled');
            button.classList.remove('disabled');
        });
    } else {
        // Handle the case where the input is not valid
        // For example, add an error class to the input's parent element

        // Disable all submit buttons and inputs
        submitters.forEach((button) => {
            button.setAttribute('disabled', 'true');
            button.classList.add('disabled');
        });
    }
}

function check_confirm_password(event, oid) {
    let tel = event.target;
    let oel = document.getElementById(oid);

    let form = tel.form;
    let valid = tel.value === oel.value;

    forms[form.id][tel.id] = valid;
    form_display_validity(form);

    console.log(tel, oel, forms[form.id][tel.id]);
}

function check_validity(event) {
    let form = event.target.form; // Get the form object that contains the input
    let input = event.target; // Get the input element that triggered the event

    forms[form.id][input.id] = input.checkValidity();

    form_display_validity(form);
}

function form_input_listener(event) {
    check_validity(event);
}

function form_submit_listener(event) {
    event.preventDefault();
    submit_form(event.target.form);
}

document.getElementById('login-form').addEventListener('input', form_input_listener);
document.getElementById('login-form').addEventListener('submit', form_submit_listener);
