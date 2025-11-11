/* -------------------------------------------------------------
   Auto font-size adjustment for card text
   ------------------------------------------------------------- */
(() => {

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

// waits for DOM layout to stabilize before running
function waitForLayoutStable(selector, callback, maxTries = 50) {
    const container = document.querySelector(selector) || document.body;
    if (!container) {
        console.warn("No container found:", selector);
        return;
    }

    let tries = 0;
    let lastHeight = container.scrollHeight;

    const interval = setInterval(() => {
        const newHeight = container.scrollHeight;
        const diff = Math.abs(newHeight - lastHeight);

        if (diff < 0.25) {
            clearInterval(interval);
            console.log("Layout stabilized — final sizing pass");
            callback();
        } else if (++tries > maxTries) {
            clearInterval(interval);
            console.warn("Layout not stable, forcing callback");
            callback();
        }
        lastHeight = newHeight;
    }, 100);
}

function isOverflowing(el) {
    return el.scrollHeight > el.clientHeight + 2 || el.scrollWidth > el.clientWidth + 2;
}

function autoSizeCardText(card) {
    const body = card.querySelector('.card-body, .card-content');
    if (!body) return;

    let minFont = 6;
    let maxFont = 10;
    let bestFit = minFont;
    let iteration = 0;

    while (maxFont - minFont > 0.01 && iteration++ < 42) {
        const mid = (minFont + maxFont) / 2;
        body.style.fontSize = mid + "pt";

        const overflowing = isOverflowing(body);
        if (overflowing) {
            maxFont = mid; // too big
        } else {
            bestFit = mid; // fits, try bigger
            minFont = mid;
        }
    }

    // bestFit = bestFit - 0.1;
    body.style.fontSize = bestFit.toFixed(2) + "pt";

    console.log(`→ ${card.className.includes('card-single') ? 'single' : card.className.includes('wide-2') ? 'double' : 'triple'} card final font ${bestFit.toFixed(2)}pt`);
}

const autoSizeAll = throttle(() => {
    const cards = document.querySelectorAll('.card-single, .card-wide');
    if (!cards.length) {
        console.warn("No cards found for autosizing");
        return;
    }

    let singles = 0, doubles = 0, triples = 0;

    cards.forEach(card => {
        if (card.classList.contains('card-single')) singles++;
        else if (card.classList.contains('card-wide-2')) doubles++;
        else if (card.classList.contains('card-wide-3')) triples++;

        autoSizeCardText(card);
    });

    console.log(`Font sizing complete — singles=${singles}, doubles=${doubles}, triples=${triples}`);
}, 300);

// body is your container here
waitForLayoutStable('body', autoSizeAll);

})();
