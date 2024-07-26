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

function initModal(modal, handler = handleAnimateEnd) {
    modal = typeof modal === 'string' ? document.querySelector(modal) : modal;
    var content = modal.querySelector('.modal-content');

    stagingArea.querySelectorAll('form').forEach(function(form) {
        // Remove any existing CSRF token fields
        // var csrfField = form.querySelector('input[name="csrfmiddlewaretoken"]');
        // if (csrfField) {
        //     csrfField.remove();
        // }

        // // Append a new CSRF token field at the end of the form
        // var newCsrfField = document.createElement('input');
        // newCsrfField.setAttribute('type', 'hidden');
        // newCsrfField.setAttribute('name', 'csrfmiddlewaretoken');
        // newCsrfField.setAttribute('value', '{{ csrf_token }}');
        // form.appendChild(newCsrfField);

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
    });

    // Enable tooltips
    modalContainer.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function(tooltipElement) {
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

function animateRevealElement(el, toEl, handler = handleAnimateEnd) {
    prepareRevealElement(el, toEl, handler);
    el.classList.add('animate-transform');
}

function handleAnimationDismissEnd(event) {
    var el = event.target;

    // Remove this event listener
    el.removeEventListener('animationend', handleAnimationDismissEnd);

    moveElement(el, '#staging-area');
    // let parent = el.parentNode;
    // try {
    //     parent = document.getElementById(el.getAttribute('stage-parent'));
    // } catch(ignr) {}

    // parent.parentNode.removeChild(parent);
    // document.getElementById('staging-area').appendChild(parent);

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
        
        // Insert the content into the selected container
        container.innerHTML = content;

        // Force reflow
        void container.offsetHeight;
    } catch (error) {
        console.error('Error loading content:', error);
        container.innerHTML = '<p>Error loading content</p>'; // Optionally show an error message in the container
    }
}
