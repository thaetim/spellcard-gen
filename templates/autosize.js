/* -------------------------------------------------------------
   Auto font-size adjustment for card text (final tuned version)
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
    return el.scrollHeight > el.clientHeight + 1 || el.scrollWidth > el.clientWidth + 1;
}

function autoSizeCardText(card) {
    const isSingle = card.classList.contains('card-single');
    const textEl = card.querySelector('.card-text');
    if (!textEl) return;

    // Reset to base size
    textEl.style.fontSize = '';

    // Font range — tuned per card type
    let minFont = isSingle ? 7 : 8;
    let maxFont = isSingle ? 10 : 11;
    let bestFit = minFont;
    let iterations = 0;

    // Binary search for best fit
    while (maxFont - minFont > 0.05 && iterations++ < 50) {
        const mid = (minFont + maxFont) / 2;
        textEl.style.fontSize = mid + 'pt';
        if (isOverflowing(textEl)) maxFont = mid;
        else { bestFit = mid; minFont = mid; }
    }

    // Apply final with safety margin
    bestFit = Math.max(bestFit - 0.1, minFont);
    textEl.style.fontSize = bestFit.toFixed(2) + 'pt';

    const type = isSingle ? 'single' :
                 card.classList.contains('card-wide-2') ? 'double' : 'triple';
    console.log(`→ ${type} card final font ${bestFit.toFixed(2)}pt`);
}

const autoSizeAll = throttle(() => {
    const cards = document.querySelectorAll('.card-single, .card-wide');
    if (!cards.length) {
        console.warn("No cards found for autosizing");
        return;
    }

    let singles = 0, doubles = 0, triples = 0;

    const sorted = Array.from(cards).sort((a, b) => {
        if (a.classList.contains('card-single') && !b.classList.contains('card-single')) return -1;
        if (!a.classList.contains('card-single') && b.classList.contains('card-single')) return 1;
        return 0;
    });

    sorted.forEach(card => {
        if (card.classList.contains('card-single')) singles++;
        else if (card.classList.contains('card-wide-2')) doubles++;
        else if (card.classList.contains('card-wide-3')) triples++;

        autoSizeCardText(card);
    });

    console.log(`Font sizing complete — singles=${singles}, doubles=${doubles}, triples=${triples}`);
}, 300);

waitForLayoutStable('body', autoSizeAll);
window.addEventListener('resize', throttle(autoSizeAll, 500));

})();
