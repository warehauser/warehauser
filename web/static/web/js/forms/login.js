//  Licensed under the Apache License, Version 2.0 (the "License");
//  you may not use this file except in compliance with the License.
//  You may obtain a copy of the License at

//      https://www.apache.org/licenses/LICENSE-2.0

//  Unless required by applicable law or agreed to in writing, software
//  distributed under the License is distributed on an "AS IS" BASIS,
//  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//  See the License for the specific language governing permissions and
//  limitations under the License.

// static/web/js/forms/login.js

function removeLoginScript() {
    const scriptElement = document.getElementById('script-form-login');
    if (scriptElement) {
        scriptElement.remove();
    }
}

async function loadForgotHandler(event) {
    modal = await loadModal('modal-forgot', '/form/web/forgot/');
    animateRevealElement(modal, modalContainer);
    makeAutofocus(modal);
    removeLoginScript();
}

async function loadForgot() {
    let modal = document.querySelector('#modal-login');
    animateDismissElement(modal, loadForgotHandler);
}

async function loginSuccess(json) {
    let username = json['user'];

    let element = document.querySelector('#link-username');
    element.innerHTML = username;
    element.classList.remove('disabled-link');

    element = document.querySelector('#user-icon');
    element.setAttribute('name', 'lock-open-outline');

    element = document.querySelector('#link-logout');
    element.classList.remove('disabled');

    await loadDashboard();
}

function loginSuccessHandler(form, json) {
    formSubmitSuccessHandler(form, json, handleAnimationDismissEndRemove);
    loginSuccess(json);
    removeLoginScript();
}
