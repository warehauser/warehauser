// Copyright 2024 warehauser @ github.com

//  Licensed under the Apache License, Version 2.0 (the "License");
//  you may not use this file except in compliance with the License.
//  You may obtain a copy of the License at

//      https://www.apache.org/licenses/LICENSE-2.0

//  Unless required by applicable law or agreed to in writing, software
//  distributed under the License is distributed on an "AS IS" BASIS,
//  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//  See the License for the specific language governing permissions and
//  limitations under the License.

// warehauser.js

const langCode = getNonENLangCode();
const stagingArea = document.getElementById('staging-area');
const modalContainer = document.getElementById('modal-container');
const animateDuration = 500;

function getNonENLangCode() {
    let langCodeMatch = window.location.pathname.match(/^\/([a-z]{2})\//);
    let langCode = langCodeMatch ? langCodeMatch[1] : null;

    if (langCode == 'en') {
        return null;
    }

    return langCode;
}

function preventDefault(event) {
    if(event) {
        event.preventDefault();
    }
}

async function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function moveElement(el, np) {
    if(el === null || np === null) { return; }

    el = typeof el === 'string' ? document.querySelector(el) : el;
    np = typeof np === 'string' ? document.querySelector(np) : np;

    try {
        let sp = el.getAttribute('stage-parent');
        if(sp) {
            el = document.getElementById(sp);
        }
    } catch(ignr) {}

    el.parentNode.removeChild(el);
    np.appendChild(el);
}

function endShakeAnimation(e) {
    target = e.target;
    target.classList.remove('shake-animation')
    target.removeEventListener('animationend', endShakeAnimation)
}

function shakeFormHeader(modal) {
    let formHeader = modal.querySelector('ion-icon')
    formHeader.addEventListener('animationend', endShakeAnimation)
    formHeader.classList.add('shake-animation')
}

function setAnimationTransform(el, fromx, fromy, tox, toy, func = 'linear', duration = animateDuration, delay = 0, direction = 'forwards') {
    el = typeof el === 'string' ? document.querySelector(el) : el;

    el.style.setProperty('--translate-from-x', fromx + 'px');
    el.style.setProperty('--translate-from-y', fromy + 'px');
    el.style.setProperty('--translate-to-x', tox + 'px');
    el.style.setProperty('--translate-to-y', toy + 'px');
    el.style.setProperty('--animate-duration', duration + 'ms');
    el.style.setProperty('--animate-func', func);
    el.style.setProperty('--animate-delay', delay + 'ms');
    el.style.setProperty('--animate-direction', direction);
}

function removeAnimationTransform(el) {
    el = typeof el === 'string' ? document.querySelector(el) : el;

    el.classList.remove('animate-transform');

    el.style.setProperty('--translate-from-x', null);
    el.style.setProperty('--translate-from-y', null);
    el.style.setProperty('--translate-to-x', null);
    el.style.setProperty('--translate-to-y', null);
    el.style.setProperty('--animate-duration', null);
    el.style.setProperty('--animate-func', null);
    el.style.setProperty('--animate-delay', null);
    el.style.setProperty('--animate-direction', null);

    el.style.setProperty('top', null);
    el.style.setProperty('left', null);
}

function handleAnimateEnd(event) {
    let target = event.target;

    target.removeEventListener('animationend', handleAnimateEnd);
    removeAnimationTransform(target);
}

function prepareRevealElement(el, toEl, handler = handleAnimateEnd) {
    if(handler) {
        el.addEventListener('animationend', handler);
    }

    // Get the bounding rect
    var rect = el.getBoundingClientRect();

    var tox = 0;
    var toy = 0;

    var offscreen = null;
    try {
        offscreen = el.getAttribute('offscreen').trim().toLowerCase();
    } catch(ignr) {}

    switch(offscreen) {
        case 'top':
            toy = Math.ceil(rect.top + rect.height + 1);
            el.style.setProperty('top', (toy * (-1)) + 'px');
            setAnimationTransform(el, 0, 0, 0, toy, 'ease-out');
            break;
        case 'left':
            tox = Math.ceil(rect.left + window.innerWidth + 1);
            el.style.setProperty('left', (tox * (-1)) + 'px');
            setAnimationTransform(el, 0, 0, tox, 0, 'ease-out');
            break;
        case 'right':
            tox = Math.ceil(rect.left + window.innerWidth + 1);
            el.style.setProperty('left', tox + 'px');
            setAnimationTransform(el, 0, 0, (tox * (-1)), 0, 'ease-out');
            break;
        default:
            break;
    }

    // move element from source parent to destination parent...
    moveElement(el, toEl);
}

function animateRevealElement(el, toEl, handler = handleAnimateEnd) {
    prepareRevealElement(el, toEl, handler);
    el.classList.add('animate-transform');
    // makeAutofocus(el);
}

function handleAnimationDismissEnd(event) {
    var el = event.target;

    // Remove this event listener
    el.removeEventListener('animationend', handleAnimationDismissEnd);

    moveElement(el, '#staging-area');

    removeAnimationTransform(el);
}

function animateDismissElement(el, handler = null) {
    if (handler == null) {
        handler = handleAnimationDismissEnd
    }

    let rect = el.getBoundingClientRect();

    var tox = 0;
    var toy = 0;

    var offscreen = 'right';
    try {
        offscreen = el.getAttribute('offscreen').trim().toLowerCase();
    } catch(ignr) {}

    switch(offscreen) {
        case 'top':
            toy = Math.ceil(rect.top + rect.height + 1) * (-1);
            break;
        case 'left':
            tox = Math.ceil(rect.left + window.innerWidth + 1);
            break;
        case 'right':
            tox = Math.ceil(rect.left + window.innerWidth + 1);
            break;
        default:
            break;
    }

    el.style.setProperty('top', null);
    el.style.setProperty('left', null);

    setAnimationTransform(el, 0, 0, tox, toy, 'ease-in');
    el.addEventListener('animationend', handler);
    el.classList.add('animate-transform');
}

// Object to store timeouts
let show_hide_timeouts = {};

function passwordShowHide(toggle, id, milliseconds = 0) {
    let inputElement = document.getElementById(id);

    if (inputElement.type === 'password') {
        inputElement.type = 'text';
        toggle.setAttribute('name', 'eye-outline');
        inputElement.focus();

        if (milliseconds > 0) {
            // Automatically reset the input type to password after specified milliseconds
            show_hide_timeouts[id] = setTimeout(() => {
                inputElement.type = 'password';
                toggle.setAttribute('name', 'eye-off-outline');
                delete show_hide_timeouts[id];
            }, milliseconds);
        }
    } else {
        if (show_hide_timeouts[id] !== undefined) {
            clearTimeout(show_hide_timeouts[id]);
            delete show_hide_timeouts[id];
        }
        inputElement.type = 'password';
        toggle.setAttribute('name', 'eye-off-outline');
        inputElement.focus();
    }
}

// Loading functions
function initModal(modal, handler = handleAnimateEnd) {
    modal = typeof modal === 'string' ? document.querySelector(modal) : modal;

    modal.querySelectorAll('form').forEach(function(form) {
        // Add listeners to all the required fields within this form
        form.querySelectorAll('input[required]').forEach(function(input) {
            input.addEventListener('input', function() {
                var formIsValid = true;

                // Check if all required fields within this form are filled
                form.querySelectorAll('input[required]').forEach(function(requiredInput) {
                    if (requiredInput.value === '') {
                        formIsValid = false;
                        return false; // Exit the loop early if any field is empty
                    }
                });

                // Enable or disable all buttons within the form based on form validity
                form.querySelectorAll('button[type="submit"]').forEach(function(button) {
                    button.disabled = !formIsValid;
                });
            });
        });

        form.querySelectorAll('.input-box input[type="file"]').forEach(function(input) {
            input.classList.add('has-value');
        });

        form.querySelectorAll('.input-box input[type="email"],.input-box input[type="url"]').forEach(function(input) {
            function inputHasValueCheck() {
                if (input.value) {
                    input.classList.add('has-value');
                } else {
                    input.classList.remove('has-value');
                }
            }

            inputHasValueCheck();
            input.addEventListener('input', inputHasValueCheck);
        });

        form.querySelectorAll('.radio-group').forEach(function(group) {
            function radioGroupHasChecked() {
                if (group.querySelector('input[type="radio"]:checked')) {
                    group.classList.add('has-checked');
                } else {
                    group.classList.remove('has-checked');
                }
            }

            radioGroupHasChecked();
            group.addEventListener('change', radioGroupHasChecked);
        });
    });

    // Enable tooltips
    modal.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function(tooltipElement) {
        var tooltip = new bootstrap.Tooltip(tooltipElement);

        tooltipElement.addEventListener('show.bs.tooltip', function() {
            var parent = tooltipElement.parentNode;
            if (parent && parent.classList.contains('error')) {
                setTimeout(function() {  // Delay to ensure tooltip is created
                    var tipElement = tooltipElement.getAttribute('aria-describedby');
                    var tooltipDom = document.getElementById(tipElement);

                    if (tooltipDom) {
                        tooltipDom.classList.add('error');
                    }
                }, 0);
            }
        });
    });
}

// This function is called to dynamically load content into the current DOM
async function loadUrl(container, url) {
    container = typeof container === 'string' ? document.querySelector(container) : container;

    if(langCode) {
        url = `/${langCode}${url}`
    }

    try {
        // Fetch the content from the URL
        let response = await fetch(url);

        // Check if the response is okay
        if (!response.ok) {
            throw new Error(`HTTP error status: ${response.status}`);
        }

        // Get the response text
        let content = await response.text();

        // At this point the script tags have not been executed since the content has not been added to the DOM yet.

        // find all script tags and move them to the end of the document body
        const tmpEl = document.createElement('div');

        tmpEl.innerHTML = content;

        // Extract all script elements
        const scripts = Array.from(tmpEl.querySelectorAll('script'));

        // Remove script tags from the content
        scripts.forEach((script) => script.remove());

        // Insert the remaining content into the selected container
        container.innerHTML = tmpEl.innerHTML;

        // Append each script to the body and ensure they execute
        scripts.forEach(script => {
            const newScript = document.createElement('script');

            // Copy all attributes from the original script
            for (let attr of script.attributes) {
                newScript.setAttribute(attr.name, attr.value);
            }

            // Copy the script content if it's not an external script
            if (!newScript.src) {
                newScript.textContent = script.textContent;
            }

            document.body.appendChild(newScript);
        });

        // Force reflow
        void container.offsetHeight;
    } catch (error) {
        console.error('Error loading content:', error);
        container.innerHTML = '<p>Error loading content</p>';
    }
}

async function loadModal(id, url) {
    await loadUrl('#staging-area', url);

    let modal = document.getElementById(id);
    initModal(modal);
    return modal;
}

async function loadDashboard() {
    await loadUrl('#dashboard', '/dashboard/');
}

/* Form handling */
function getModalForForm(form) {
    return form.closest('.modal');
}

function disableForm(form) {
    form = typeof form === 'string' ? document.querySelector(form) : form;

    let elements = form.querySelectorAll('#' + form.id + ' input, #' + form.id + ' select, #' + form.id + ' textarea, #' + form.id + ' button')
    elements.forEach(function(element) {
        element.disabled = true
        element.parentElement.classList.remove('error')
    })

    elements = form.querySelectorAll('#' + form.id + ' .input-text-button ion-icon')
    elements.forEach((button) => {
        button.classList.add('disabled');
    });
}

function enableForm(form) {
    form = typeof form === 'string' ? document.querySelector(form) : form;

    let elements = form.querySelectorAll('input, select, textarea, button')
    elements.forEach(function(element) {
        element.disabled = false
    })

    elements = form.querySelectorAll('#' + form.id + ' a');
    elements.forEach((link) => {
        enableLink(link)
    });

    elements = document.querySelectorAll('#' + form.id + ' .input-text-button ion-icon')
    elements.forEach((button) => {
        button.classList.remove('disabled');
    });
}

function disableLink(link) {
    const hasFocus = document.activeElement === link;

    link.classList.add('disabled-link');
    link.setAttribute('tabindex', -1);
    link.addEventListener('click', preventDefault)

    if (hasFocus) {
        link.blur();
    }
}

function enableLink(link) {
    link.classList.remove('disabled-link');
    link.removeAttribute('tabindex');
    link.removeEventListener('click', preventDefault)
}

function disableModal(modal) {
    modal = typeof modal === 'string' ? document.querySelector(modal) : modal;

    modal.querySelectorAll('a').forEach((link) => {
        disableLink(link)
    });

    modal.querySelectorAll('form').forEach((form) => {
        disableForm(form);
    });
}

function enableModal(modal) {
    modal = typeof modal === 'string' ? document.querySelector(modal) : modal;

    modal.querySelectorAll('a').forEach((link) => {
        enableLink(link)
    });

    modal.querySelectorAll('form').forEach((form) => {
        enableForm(form);
    });
}

function displayErrors(form, json) {
    let error = json.error;

    if(!error) {
        error = '';
    }

    form.querySelector('#error-' + form.id).innerHTML = error;

    if(!json.fields) {
        json.fields = {}
    }

    form.querySelectorAll('input, textarea, select').forEach(function(inputElement) {
        const fieldName = inputElement.name;
        const boxElement = inputElement.closest('.input-box');

        // Check if there is an error for this field in the response
        if (json.fields[fieldName]) {
            // Find or create the error message element
            if(boxElement) {
                boxElement.classList.add('error');
            }

            let errorElement = inputElement.parentElement.querySelector('.error-message');

            if (!errorElement) {
                errorElement = document.createElement('div');
                errorElement.id = 'id-' + inputElement.id;
                errorElement.className = 'error error-message';
                inputElement.parentElement.appendChild(errorElement);
            }

            // Set the error message
            errorElement.textContent = json.fields[fieldName];
        } else {
            // Optionally, clear any previous error messages if the field has no errors
            if(boxElement) {
                boxElement.classList.remove('error');
            }

            let errorElement = inputElement.parentElement.querySelector('.error-message');
            if (errorElement) {
                errorElement.textContent = '';
            }
        }
    });
}

function clearErrors(form) {
    displayErrors(form, {});
}

function makeAutofocus(form) {
    form = typeof form === 'string' ? document.querySelector(form) : form;

    if (!form) return;

    const autoFocusElements = form.querySelectorAll('[autofocus]');
    if (autoFocusElements.length > 0) {
        const autoFocusElement = autoFocusElements[0];

        // Check if the element already has focus
        if (document.activeElement !== autoFocusElement) {
            autoFocusElement.focus();
        }

        // Select the content of the element regardless
        autoFocusElement.select();
    }
}

async function submitForm(event, form, url, success = formSubmitSuccessHandler, fail = formSubmitFailHandler) {
    preventDefault(event);

    form = typeof form === 'string' ? document.querySelector(form) : form;
    if(!form) {
        return false
    }

    disableModal(getModalForForm(form));
    clearErrors(form);

    formData = new FormData();
    fields = form.querySelectorAll('input, textarea, select')
    fields.forEach((field) => {
        field.parentElement.classList.remove('error');
        field.disabled = true;

        formData.append(field.name, field.value);
    });

    await fetch(url, {
        method: form.method,
        body: formData
    }).then((response) => {
        if(response.ok) {
            // Successful login
            response.json().then((json) => {
                success(form, json);
            });
        } else {
            response.json().then((json) => {
                fail(form, json);
            });
        }
    });

    return false;
}

function handleAnimationDismissEndRemove(event) {
    var el = event.target;
    el.remove();
}

function formSubmitSuccessHandler(form, json, handler = null) {
    let modal = getModalForForm(form);
    animateDismissElement(modal, handler);
}

function formSubmitFailHandler(form, json) {
    setTimeout(() => {
        let modal = getModalForForm(form);
        let header = modal.querySelector('.modal-header');

        displayErrors(form, json);
        shakeFormHeader(header);
        enableModal(modal);
        makeAutofocus(form);
    }, 1000);
}

function forgotSuccessHandler(form, json) {
    console.log('forgotSuccessHandler called');
}
