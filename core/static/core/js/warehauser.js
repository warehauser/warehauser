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

function show_card_modal(event, id) {
    let card = document.getElementById(id);
    card.style.display = 'block';
}

function animate_move_element(element, deltaX, deltaY, func = 'ease-in-out', transitionend = null, animate_time = null) {
    element.style.setProperty('--deltaX', `${deltaX}px`)
    element.style.setProperty('--deltaY', `${deltaY}px`)
    element.style.setProperty('--animate-function', func)

    if(transitionend !== null && transitionend !== undefined) {
        element.addEventListener('transitionend', transitionend)
    }

    if(animate_time !== null && animate_time !== undefined) {
        element.style.setProperty('--animate-time', `${animate_time}ms`)
    }

    element.classList.add('animate-move')
}

function animate_move_remove_styles(element) {
    element.style.setProperty('--deltaX', '')
    element.style.setProperty('--deltaY', '')
    element.style.setProperty('--animate-time', '')
    element.style.setProperty('--animate-function', '')
}

function animate_move_dismiss_end_listener(e) {
    let element = e.target
    element.style.visibility = 'hidden'
    element.removeEventListener('transitionend', animate_move_dismiss_end_listener)
}

function animate_move_reveal_end_listener(e) {
    let element = e.target
    element.removeEventListener('transitionend', animate_move_reveal_end_listener)
    element.classList.remove('animate-move')
    animate_move_remove_styles(element)
}

function animate_move_element_reveal(id) {
    let element = document.getElementById(id)
    if (!element) {
        return
    }

    // Ensure visibility is restored
    element.style.visibility = 'visible'

    // reverse the animate-move class direction
    animate_move_element(element, 0, 0, 'ease-out', animate_move_reveal_end_listener)
}

function animate_move_element_dismiss_top(id) {
    let element = document.getElementById(id)
    if (!element) {
        return
    }

    // Calculate the new position to move the element off screen at the top by just 1 pixel
    let rect = element.getBoundingClientRect()
    let positionY = 1 - rect.top - rect.height

    animate_move_element(element, 0, positionY, 'ease-in', animate_move_dismiss_end_listener)
}

function animate_move_element_dismiss_left(id) {
    let element = document.getElementById(id)
    if (!element) {
        return
    }

    // Calculate the new position to move the element off screen at the left by just 1 pixel
    let rect = element.getBoundingClientRect()
    let positionX = 1 - rect.left - rect.width

    animate_move_element(element, positionX, 0, 'ease-in', animate_move_dismiss_end_listener)
}

function animate_move_element_dismiss_right(id) {
    let element = document.getElementById(id)
    if (!element) {
        return
    }

    // Calculate the new position to move the element off screen at the right by just 1 pixel
    let rect = element.getBoundingClientRect()
    let positionX = window.innerWidth - rect.right + 1

    animate_move_element(element, positionX, 0, 'ease-in', animate_move_dismiss_end_listener)
}

async function load_card(id, url) {
    let card = document.getElementById(id);
    if(!card) {
        return;
    }

    let response = await fetch(url);
    let content = await response.text();

    card.innerHTML = content;
}

















function make_autofocus(containerId) {
    const container = document.getElementById(containerId)
    if (!container) return

    const autoFocusElements = container.querySelectorAll('[autofocus]');
    if (autoFocusElements.length > 0) {
        autoFocusElements[0].focus()
        autoFocusElements[0].select()
    }
}

function reveal_card(id) {
    let first_click = true
    let focused = false

    let element = document.getElementById(id);
    if(!element) {
        return
    }

    function dismiss_card() {
        forms = document.querySelectorAll('#' + id + ' form')
        forms.forEach((form) => {
            disable_form(form)
        })
        element.classList.remove('reveal');
        window.removeEventListener('blur', blur_el)
        window.removeEventListener('focus', focus_el)
        window.removeEventListener('click', click_el)
        window.removeEventListener('keydown', keydown_el)

        enable_link(document.getElementById('login-link'))
    }

    function blur_el(event) {
        // first_click = true
        focused = false
    }

    function focus_el(event) {
        focused = true
    }

    function click_el(event) {
        if (first_click || focused) {
            first_click = false
            focused = false
            return
        }

        if (!element.contains(event.target)) {
            dismiss_card()
        }
    }

    function keydown_el(event) {
        if (event.key === 'Escape') {
            dismiss_card()
        }
    }

    element.classList.add('reveal')

    window.addEventListener('blur', blur_el)
    window.addEventListener('focus', focus_el)
    window.addEventListener('click', click_el);
    window.addEventListener('keydown', keydown_el)

    window.addEventListener('unload', () => {
        window.removeEventListener('blur', blur_el)
        window.removeEventListener('focus', focus_el)
        window.removeEventListener('click', click_el)
        window.removeEventListener('keydown', keydown_el)
    })

    element.querySelectorAll('form').forEach((form) => {
        enable_form(form)
    })

    make_autofocus(id)
}

function do_login_click(event) {
    event.preventDefault()
    let link = document.getElementById('login-link')
    disable_link(link)
    reveal_card('card-login-form')
}

function position_card_init(id) {
    const card = document.getElementById(id)
    if (!card) {
        return
    }

    const rect = card.getBoundingClientRect()
    const header = document.getElementById('header')
    const footer = document.getElementById('footer')

    function position_card() {
        let viewWidth = window.innerWidth
        let viewHeight = window.innerHeight

        let headerHeight = header.getBoundingClientRect().height
        let footerHeight = footer.getBoundingClientRect().height

        let hideTop = 0 - rect.height - headerHeight
        let hideLeft = 0 - rect.width
        let hideRight = viewWidth

        let horizontalCenter = (viewWidth - rect.width) / 2
        let verticalCenter = (viewHeight - rect.height) / 2 - hideTop
        verticalCenter = rect.height + headerHeight * 2 + 100

        card.style.setProperty('--position-top', `${verticalCenter}px`)
        card.style.setProperty('--position-left', `${horizontalCenter}px`)

        card.style.setProperty('--hide-top', `${hideTop}px`)
        card.style.setProperty('--hide-left', `${hideLeft}px`)
        card.style.setProperty('--hide-right', `${hideRight}px`)
    }

    position_card()

    window.addEventListener('resize', position_card)

    window.addEventListener('unload', () => {
        window.removeEventListener('resize', position_card)
    })
}

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

    form.addEventListener('input', form_input_listener);
    form.addEventListener('submit', form_submit_listener);
}

function enable_link(link) {
    link.classList.remove('disabled-link');
    link.removeAttribute('tabindex');
    link.removeEventListener('click', prevent_default)
}

function enable_link_by_id(id) {
    enable_link(document.getElementById(id))
}

function disable_link(link) {
    const hasFocus = document.activeElement === link;

    link.classList.add('disabled-link');
    link.setAttribute('tabindex', -1);
    link.addEventListener('click', prevent_default)

    if (hasFocus) {
        link.blur();
    }
}

function disable_link_by_id(id) {
    disable_link(document.getElementById(id))
}

function disable_form(form) {
    let elements = form.querySelectorAll('#' + form.id + ' input, #' + form.id + ' select, #' + form.id + ' textarea, #' + form.id + ' button')
    elements.forEach(function(element) {
        element.disabled = true
        element.parentElement.classList.remove('error')
    })

    elements = form.querySelectorAll('#' + form.id + ' a');
    elements.forEach((link) => {
        disable_link(link)
    });

    elements = form.querySelectorAll('#' + form.id + ' .input-text-button ion-icon')
    elements.forEach((button) => {
        button.classList.add('disabled');
    });
}

function disable_form_by_id(id) {
    disable_form(document.getElementById(id))
}

function enable_form(form) {
    let elements = document.querySelectorAll('#' + form.id + ' input, #' + form.id + ' select, #' + form.id + ' textarea, #' + form.id + ' button')
    elements.forEach(function(element) {
        element.disabled = false
    })

    elements = form.querySelectorAll('#' + form.id + ' a');
    elements.forEach((link) => {
        enable_link(link)
    });

    elements = document.querySelectorAll('#' + form.id + ' .input-text-button ion-icon')
    elements.forEach((button) => {
        button.classList.remove('disabled');
    });
}

function enable_form_by_id(id) {
    enable_form(document.getElementById(id))
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
        document.documentElement.style.setProperty('--target-rect-top', offsetTop + 'px');

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

function prevent_default(event) {
    event.preventDefault()
}

async function submit_login_form(id) {
    form = document.getElementById(id)
    if(!form) {
        return false
    }

    disable_form_by_id(id)

    formData = new FormData();
    fields = form.querySelectorAll('input, textarea')
    fields.forEach((field) => {
        field.parentElement.classList.remove('error');
        field.disabled = true;

        formData.append(field.name, field.value);
    });

    let response = await fetch('/auth/login/', {
        method: form.method,
        body: formData
    }).then((response) => {
// console.log(response)
        if(response.ok) {
            // We are logged in! :-)
            show_logged_in(form);
        } else {
            setTimeout(() => {
                shake_form_header(form);
                enable_form_by_id(id)
                make_autofocus(id)
            }, 1500)
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
            button.setAttribute('disabled', 'true')
            button.classList.add('disabled')
        })
    }
}

function check_confirm_password(event, oid) {
    let tel = event.target
    let oel = document.getElementById(oid)

    let form = tel.form
    let valid = tel.value === oel.value

    forms[form.id][tel.id] = valid
    form_display_validity(form)

    console.log(tel, oel, forms[form.id][tel.id])
}

function check_validity(event) {
    let form = event.target.form // Get the form object that contains the input
    let input = event.target // Get the input element that triggered the event

    forms[form.id][input.id] = input.checkValidity()

    form_display_validity(form)
}

function form_input_listener(event) {
    check_validity(event)
}

function form_submit_listener(event) {
    event.preventDefault()
    submit_form(event.target.form)
}
