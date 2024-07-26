// Copyright 2024 warehauser @ github.com

// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at

//     https://www.apache.org/licenses/LICENSE-2.0

// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// js/classes.js

export class DynamicElement {
    constructor(el) {
        this.el = el;
    }

    replace(id) {
        // Replace the contents (innerHTML) of the tag found using the id as the query selector from the document
        const targetElement = document.querySelector(id);
        if (targetElement) {
            targetElement.innerHTML = this.el.outerHTML;
        } else {
            console.error(`Element with selector ${id} not found.`);
        }
    }

    append(id, after = null) {
        // id is the query selector of the document in which to insert this element
        // after is the query selector of the children of the id element after which this.el should be inserted,
        // or if '' then insert as first child of id element, or if null/not supplied then append to the end
        const parentElement = document.querySelector(id);
        if (parentElement) {
            if (after === '') {
                parentElement.insertBefore(this.el, parentElement.firstChild);
            } else if (after) {
                const referenceElement = parentElement.querySelector(after);
                if (referenceElement) {
                    referenceElement.insertAdjacentElement('afterend', this.el);
                } else {
                    console.error(`Reference element with selector ${after} not found.`);
                }
            } else {
                parentElement.appendChild(this.el);
            }
        } else {
            console.error(`Parent element with selector ${id} not found.`);
        }
    }

    remove() {
        // remove this.el from the DOM
        if (this.el && this.el.parentNode) {
            this.el.parentNode.removeChild(this.el);
        } else {
            console.error(`Element ${this.el} is not in the DOM.`);
        }
    }
}
