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

export class AnimateElement {
    constructor(el) {
        this.el = el;
        this.animationQueue = [];
        this.handleAnimationEnd = this.handleAnimationEnd.bind(this);
    }

    setQueue(queue) {
        this.animationQueue = queue;
console.log(queue);
console.log(this.animationQueue);
    }

    next() {
console.log('move called.', this.animationQueue.length, this.animationQueue);
        if (this.animationQueue.length > 0) {
            let oper = this.animationQueue.shift();

            let fromx = oper.fromx !== null ? oper.fromx : parseFloat(this.el.style.getPropertyValue('--translate-to-x')) || 0;
            let fromy = oper.fromy !== null ? oper.fromy : parseFloat(this.el.style.getPropertyValue('--translate-to-y')) || 0;

console.log('fromx:', fromx, 'fromy:', fromy);

            this.el.style.setProperty('--translate-from-x', fromx + 'px');
            this.el.style.setProperty('--translate-from-y', fromy + 'px');
            this.el.style.setProperty('--translate-to-x', oper.tox + 'px');
            this.el.style.setProperty('--translate-to-y', oper.toy + 'px');
            this.el.style.setProperty('--animate-time', oper.time + 'ms');
            this.el.style.setProperty('--animate-func', oper.func);
            this.el.style.setProperty('--animate-delay', oper.delay + 'ms');
            this.el.style.setProperty('--animate-direction', oper.direction);

            this.el.currentAnimationHandler = oper.handler;
            this.el.addEventListener('animationend', this.handleAnimationEnd);
console.log('added listener.');
            this.el.classList.add('animate-transform');
        }
    }

    handleAnimationEnd(event) {
console.log('handleAnimationEnd called.');
        // Update the from coordinates to be the to coordinates for the next animation
        // this.el.style.setProperty('--translate-from-x', this.el.style.getPropertyValue('--translate-to-x'));
        // this.el.style.setProperty('--translate-from-y', this.el.style.getPropertyValue('--translate-to-y'));

        event.target.removeEventListener('animationend', this.handleAnimationEnd);
console.log('removed listener.');
        event.target.classList.remove('animate-transform');
        if (this.el.currentAnimationHandler) {
            this.el.currentAnimationHandler();
        }
console.log(this.animationQueue.length, this.animationQueue);
        this.next(); // Trigger the next animation in the queue
    }
}

export class AnimateElement2 {
    constructor(el) {
        this.el = el;
        this.isAnimating = false;
        this.animationQueue = [];

        this.handleAnimationRevealEnd = this.handleAnimationRevealEnd.bind(this);
        this.handleAnimationDismissEnd = this.handleAnimationDismissEnd.bind(this);
        this.handleAnimationMoveEnd = this.handleAnimationMoveEnd.bind(this);
        this.doNextAnimation = this.doNextAnimation.bind(this);
    }

    setFromCoords(fromx, fromy) {
        this.el.style.setProperty('--translate-from-x', fromx + 'px');
        this.el.style.setProperty('--translate-from-y', fromy + 'px');
    }

    setOffscreenCoords() {
        const originalCss = {
            visibility: this.el.style.visibility,
            display: this.el.style.display,
            position: this.el.style.position,
            top: this.el.style.top,
            left: this.el.style.left
        };

        this.el.style.visibility = 'hidden';
        this.el.style.display = 'block';
        this.el.style.position = 'absolute';

        const rect = this.el.getBoundingClientRect();

        this.el.style.visibility = originalCss.visibility;
        this.el.style.display = originalCss.display;
        this.el.style.position = originalCss.position;
        this.el.style.top = originalCss.top;
        this.el.style.left = originalCss.left;

        let fromx = 0;
        let fromy = 0;

        let offscreen = 'right';
        try {
            offscreen = this.el.getAttribute('offscreen').trim().toLowerCase();
        } catch (ignr) {}

        switch (offscreen) {
            case 'top':
                fromy = (rect.top + rect.height + 1) * -1;
                break;
            case 'left':
                fromx = (rect.left + window.innerWidth + 1) * -1;
                break;
            case 'right':
                fromx = rect.left + window.innerWidth + 1;
                break;
            default:
                break;
        }

        this.setFromCoords(fromx, fromy);
    }

    setAnimationVariables(tox, toy, delay, time, func, direction) {
        this.el.style.setProperty('--translate-to-x', tox);
        this.el.style.setProperty('--translate-to-y', toy);
        this.el.style.setProperty('--animate-delay', delay);
        this.el.style.setProperty('--animate-time', time);
        this.el.style.setProperty('--animate-func', func);
        this.el.style.setProperty('--animate-direction', direction);
    }

    animateTransform(tox, toy, time, delay, func, direction = 'forwards', handler = null) {
        if (this.animationQueue.length > 0) {
            this.animationQueue.push({ tox, toy, delay, time, func, direction, handler });
        } else {
            this.isAnimating = true;
            this.setAnimationVariables(tox, toy, delay, time, func, direction);
            if (handler) {
                this.el.addEventListener('animationend', handler);
            }
            this.el.classList.add('animate-transform');
        }
    }

    doNextAnimation() {
        this.isAnimating = false;

        if (this.animationQueue.length > 0) {
            let nextAnimation = this.animationQueue.shift();
            this.move(
                parseFloat(nextAnimation.tox),
                parseFloat(nextAnimation.toy),
                nextAnimation.time,
                nextAnimation.delay,
                nextAnimation.func,
                nextAnimation.direction,
                nextAnimation.handler
            );
        }
    }

    cancelAnimation() {
        this.el.classList.remove('animate-transform');
    }

    reveal() {
        this.el.classList.remove('d-none');
        this.animateTransform('0px', '0px', '500ms', 'ease-out', '0ms', 'forwards', this.handleAnimationRevealEnd);
    }

    dismiss() {
        this.animateTransform('0px', '0px', '500ms', 'ease-in', '0ms', 'reverse', this.handleAnimationDismissEnd);
    }

    move(tox, toy, ms = 0, delay = 0, fn = 'linear', direction = 'forwards', handler = this.handleAnimationMoveEnd) {
        this.animateTransform(tox + 'px', toy + 'px', ms + 'ms', fn, delay + 'ms', direction, handler);
    }

    handleAnimationRevealEnd(event) {
        this.cancelAnimation();
        event.target.removeEventListener('animationend', this.handleAnimationRevealEnd);
        this.doNextAnimation();
    }

    handleAnimationDismissEnd(event) {
        event.target.classList.add('d-none');
        this.cancelAnimation();
        event.target.removeEventListener('animationend', this.handleAnimationDismissEnd);
        this.doNextAnimation();
    }

    handleAnimationMoveEnd(event) {
        // Get the current translate-to-x and translate-to-y values
console.log(this.el.style.getPropertyValue('--translate-to-x'));
        const tox = parseFloat(this.el.style.getPropertyValue('--translate-to-x')) || 0;
        const toy = parseFloat(this.el.style.getPropertyValue('--translate-to-y')) || 0;
console.log(this.el.style.getPropertyValue('--translate-to-x'));

        // Set these values as the new from coordinates
        this.setFromCoords(tox, toy);

        // Remove the event listener
        event.target.removeEventListener('animationend', this.handleAnimationMoveEnd);

        // Mark as not animating and start the next animation if there is any
        // this.cancelAnimation();
        this.doNextAnimation();
    }
}


















export class AnimateElementOld {
    constructor(el) {
        this.el = el;
        this.isAnimating = false;
        this.animationQueue = [];

        this.handleAnimationRevealEnd = this.handleAnimationRevealEnd.bind(this);
        this.handleAnimationDismissEnd = this.handleAnimationDismissEnd.bind(this);
        this.handleAnimationMoveEnd = this.handleAnimationMoveEnd.bind(this);

        this.doNextAnimation = this.doNextAnimation.bind(this);
    }

    setFromCoords(fromx, fromy) {
        this.el.style.setProperty('--translate-from-x', fromx + 'px');
        this.el.style.setProperty('--translate-from-y', fromy + 'px');
    }

    setOffscreenCoords() {
        // Save the original CSS properties
        var originalCss = {
            visibility: this.el.style.visibility,
            display: this.el.style.display,
            position: this.el.style.position,
            top: this.el.style.top,
            left: this.el.style.left
        };

        // Apply new CSS properties to make the content invisible and above the top of the screen
        this.el.style.visibility = 'hidden';
        this.el.style.display = 'block';
        this.el.style.position = 'absolute';

        // Get the bounding rect
        var rect = this.el.getBoundingClientRect();

        // this.el.classList.add('d-none');

        // Restore the original CSS properties
        this.el.style.visibility = originalCss.visibility;
        this.el.style.display = originalCss.display;
        this.el.style.position = originalCss.position;
        this.el.style.top = originalCss.top;
        this.el.style.left = originalCss.left;

        var fromx = 0;
        var fromy = 0;

        var offscreen = 'right';
        try {
            offscreen = this.el.getAttribute('offscreen').trim().toLowerCase();
        } catch(ignr) {}

        switch(offscreen) {
            case 'top':
                fromy = (rect.top + rect.height + 1) * (-1);
                break;
            case 'left':
                fromx = (rect.left + window.innerWidth + 1) * (-1);
                break;
            case 'right':
                fromx = rect.left + window.innerWidth + 1;
                break;
            default:
                break;
        }

        this.setFromCoords(fromx, fromy);
    }

    setAnimationVariables(tox, toy, time, func, delay, direction) {
        this.el.style.setProperty('--translate-to-x', tox);
        this.el.style.setProperty('--translate-to-y', toy);
        this.el.style.setProperty('--animate-time', time);
        this.el.style.setProperty('--animate-func', func);
        this.el.style.setProperty('--animate-delay', delay);
        this.el.style.setProperty('--animate-direction', direction);
    }

    animateTransform(tox, toy, time, func, delay, direction, handler = null) {
        if (this.isAnimating) {
console.log('Currently animating. Adding to the queue.');
            // Add to queue if already animating
            this.animationQueue.push({ tox, toy, time, func, delay, direction, handler });
        } else {
console.log('Animating!');
            this.isAnimating = true;
            this.setAnimationVariables(tox, toy, time, func, delay, direction);
            if(handler) {
                this.el.addEventListener('animationend', handler);
            }
            this.el.classList.add('animate-transform');
        }
    }

    doNextAnimation() {
        this.isAnimating = false;

        // Check if there are more animations in the queue
        if (this.animationQueue.length > 0) {
            const nextAnimation = this.animationQueue.shift();
console.log('doNextAnimation', nextAnimation);
            this.animateTransform(
                nextAnimation.tox,
                nextAnimation.toy,
                nextAnimation.time,
                nextAnimation.func,
                nextAnimation.delay,
                nextAnimation.direction,
                nextAnimation.handler
            );
        }
    }

    cancelAnimation() {
        this.el.classList.remove('animate-transform');
    }

    reveal() {
        this.el.classList.remove('d-none');
        this.animateTransform('0px', '0px', '500ms', 'ease-out', '0ms', 'forwards', this.handleAnimationRevealEnd);
    }

    dismiss() {
        this.animateTransform('0px', '0px', '500ms', 'ease-in', '0ms', 'reverse', this.handleAnimationDismissEnd);
    }

    move(tox, toy, ms = 0, delay = 0, fn = 'linear') {
        this.animateTransform(tox + 'px', toy + 'px', ms + 'ms', fn, delay + 'ms', 'forwards', this.handleAnimationMoveEnd);
    }

    handleAnimationRevealEnd(event) {
        // Add any logic that needs to run after reveal animation ends
//        event.target.classList.remove('animate-transform');
        this.cancelAnimation();
        event.target.removeEventListener('animationend', this.handleAnimationRevealEnd);
        this.doNextAnimation();
    }

    handleAnimationDismissEnd(event) {
        // Add any logic that needs to run after dismiss animation ends
        event.target.classList.add('d-none');
        this.cancelAnimation();
//        event.target.classList.remove('animate-transform');
        event.target.removeEventListener('animationend', this.handleAnimationDismissEnd);
        this.doNextAnimation();
    }

    handleAnimationMoveEnd(event) {
        // Add any logic that needs to run after dismiss animation ends
        const tox = this.el.style.getPropertyValue('--translate-to-x');
        const toy = this.el.style.getPropertyValue('--translate-to-y');
        this.setFromCoords(parseFloat(tox), parseFloat(toy));

        event.target.removeEventListener('animationend', this.handleAnimationMoveEnd);
        this.doNextAnimation();
    }
}

export class FormHandler {
    constructor(form) {
        this.form = form;
    }
}
