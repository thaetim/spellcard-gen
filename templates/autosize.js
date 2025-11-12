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
    // Consistent tolerance for all card types
    const tolerance = 2;
    return el.scrollHeight > el.clientHeight + tolerance || el.scrollWidth > el.clientWidth + tolerance;
}

function calculateOptimalFontSize(card) {
    const cardContent = card.querySelector('.card-content');
    if (!cardContent) return null;

    // Use let instead of const for variables that need to be reassigned
    let minFont = 6;
    let maxFont = 10;

    let bestFit = minFont;
    let iteration = 0;

    // Reset to test at max font first
    cardContent.style.fontSize = maxFont + "pt";

    // Binary search for optimal size
    const precision = 0.05;
    while (maxFont - minFont > precision && iteration++ < 100) {
        const mid = (minFont + maxFont) / 2;
        cardContent.style.fontSize = mid + "pt";

        if (isOverflowing(cardContent)) {
            maxFont = mid - precision;
        } else {
            bestFit = mid;
            minFont = mid + precision;
        }
    }

    // Apply safety margin
    const safetyMargin = 0.1;
    bestFit = Math.max(bestFit - safetyMargin, minFont);

    // Final overflow check with emergency reduction
    let emergencyTries = 0;
    while (isOverflowing(cardContent) && emergencyTries < 25 && bestFit > minFont) {
        bestFit = bestFit - 0.15;
        cardContent.style.fontSize = bestFit.toFixed(2) + "pt";
        emergencyTries++;
    }

    return bestFit;
}

function applyFontSizeToCard(card, fontSize) {
    const cardContent = card.querySelector('.card-content');
    if (cardContent) {
        cardContent.style.fontSize = fontSize.toFixed(2) + "pt";
    }
}

function autoSizeAllCards() {
    const cards = document.querySelectorAll('.card-single, .card-double, .card-triple');
    if (!cards.length) {
        console.warn("No cards found for autosizing");
        return;
    }

    let singles = 0, doubles = 0, triples = 0;

    // Calculate and apply optimal sizes for all cards
    cards.forEach(card => {
        if (card.classList.contains('card-single')) {
            singles++;
        } else if (card.classList.contains('card-double')) {
            doubles++;
        } else if (card.classList.contains('card-triple')) {
            triples++;
        }

        const optimalSize = calculateOptimalFontSize(card);
        if (optimalSize !== null) {
            applyFontSizeToCard(card, optimalSize);
            
            const cardContent = card.querySelector('.card-content');
            const cardType = card.classList.contains('card-single') ? 'single' : 
                            card.classList.contains('card-double') ? 'double' : 'triple';
            console.log(`→ ${cardType} card final font ${optimalSize.toFixed(2)}pt ${isOverflowing(cardContent) ? '(OVERFLOWING!)' : ''}`);
        }
    });

    console.log(`Font sizing complete — singles=${singles}, doubles=${doubles}, triples=${triples}`);
}

const autoSizeAll = throttle(() => {
    autoSizeAllCards();
}, 300);

// Run on load and on resize
waitForLayoutStable('body', autoSizeAll);
window.addEventListener('resize', throttle(autoSizeAll, 500));

})();