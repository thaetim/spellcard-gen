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
    // Tighter tolerance for single cards
    const tolerance = el.closest('.card-single') ? 0.5 : 2;
    return el.scrollHeight > el.clientHeight + tolerance || el.scrollWidth > el.clientWidth + tolerance;
}

function autoSizeCardText(card) {
    const isSingleCard = card.classList.contains('card-single');
    
    // For single cards, target .card-text specifically
    // For multi-cards, target .card-content which has columns
    const body = isSingleCard 
        ? card.querySelector('.card-body')
        : card.querySelector('.card-content');
    
    if (!body) return;

    // Different strategies for single vs multi cards
    let minFont, maxFont;
    
    if (isSingleCard) {
        minFont = 4.5;
        maxFont = 9;
    } else {
        // Multi-cards can use more space
        minFont = 6;
        maxFont = 10;
    }

    let bestFit = minFont;
    let iteration = 0;

    // Reset to test at max font first
    body.style.fontSize = maxFont + "pt";

    // Binary search for optimal size
    const precision = isSingleCard ? 0.1 : 0.05;
    while (maxFont - minFont > precision && iteration++ < 100) {
        const mid = (minFont + maxFont) / 2;
        body.style.fontSize = mid + "pt";

        if (isOverflowing(body)) {
            maxFont = mid - 0.05;
        } else {
            bestFit = mid;
            minFont = mid + 0.05;
        }
    }

    // Apply final size with small safety margin
    const safetyMargin = isSingleCard ? 0.15 : 0.1;
    bestFit = Math.max(bestFit - safetyMargin, minFont);
    body.style.fontSize = bestFit.toFixed(2) + "pt";

    // Final overflow check
    let emergencyTries = 0;
    while (isOverflowing(body) && emergencyTries < 30 && bestFit > minFont) {
        bestFit = bestFit - 0.15;
        body.style.fontSize = bestFit.toFixed(2) + "pt";
        emergencyTries++;
    }

    const cardType = isSingleCard ? 'single' : 
                    card.classList.contains('card-wide-2') ? 'double' : 'triple';
    console.log(`→ ${cardType} card final font ${bestFit.toFixed(2)}pt ${isOverflowing(body) ? '(OVERFLOWING!)' : ''}`);
}

const autoSizeAll = throttle(() => {
    const cards = document.querySelectorAll('.card-single, .card-wide');
    if (!cards.length) {
        console.warn("No cards found for autosizing");
        return;
    }

    let singles = 0, doubles = 0, triples = 0;

    // Process single cards first since they're more constrained
    const sortedCards = Array.from(cards).sort((a, b) => {
        if (a.classList.contains('card-single') && !b.classList.contains('card-single')) return -1;
        if (!a.classList.contains('card-single') && b.classList.contains('card-single')) return 1;
        return 0;
    });

    sortedCards.forEach(card => {
        if (card.classList.contains('card-single')) singles++;
        else if (card.classList.contains('card-wide-2')) doubles++;
        else if (card.classList.contains('card-wide-3')) triples++;

        autoSizeCardText(card);
    });

    console.log(`Font sizing complete — singles=${singles}, doubles=${doubles}, triples=${triples}`);
}, 300);

// Run on load and on resize
waitForLayoutStable('body', autoSizeAll);
window.addEventListener('resize', throttle(autoSizeAll, 500));

})();