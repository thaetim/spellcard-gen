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

function calculateOptimalFontSize(card) {
    const isSingleCard = card.classList.contains('card-single');
    
    // For single cards, target .card-text specifically
    // For multi-cards, target .card-content which has columns
    const body = isSingleCard 
        ? card.querySelector('.card-body')
        : card.querySelector('.card-content');
    
    if (!body) return null;

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

    // Apply small safety margin
    const safetyMargin = isSingleCard ? 0.15 : 0.1;
    bestFit = Math.max(bestFit - safetyMargin, minFont);

    // Final overflow check with emergency reduction
    let emergencyTries = 0;
    while (isOverflowing(body) && emergencyTries < 8 && bestFit > minFont) {
        bestFit = bestFit - 0.15;
        body.style.fontSize = bestFit.toFixed(2) + "pt";
        emergencyTries++;
    }

    return bestFit;
}

function applyFontSizeToCard(card, fontSize) {
    const isSingleCard = card.classList.contains('card-single');
    const body = isSingleCard 
        ? card.querySelector('.card-body')
        : card.querySelector('.card-content');
    
    if (body) {
        body.style.fontSize = fontSize.toFixed(2) + "pt";
    }
}

function autoSizeAllCards() {
    const cards = document.querySelectorAll('.card-single, .card');
    if (!cards.length) {
        console.warn("No cards found for autosizing");
        return;
    }

    let singles = 0, doubles = 0, triples = 0;
    const singleCardOptimalSizes = [];

    // First pass: calculate optimal sizes for all cards
    const sortedCards = Array.from(cards).sort((a, b) => {
        if (a.classList.contains('card-single') && !b.classList.contains('card-single')) return -1;
        if (!a.classList.contains('card-single') && b.classList.contains('card-single')) return 1;
        return 0;
    });

    // Calculate optimal sizes without applying them yet
    sortedCards.forEach(card => {
        if (card.classList.contains('card-single')) {
            singles++;
            const optimalSize = calculateOptimalFontSize(card);
            if (optimalSize !== null) {
                singleCardOptimalSizes.push(optimalSize);
            }
        } else if (card.classList.contains('card-double')) {
            doubles++;
        } else if (card.classList.contains('card-triple')) {
            triples++;
        }
    });

    // For single cards, find the minimum optimal size and apply it to all
    const minSingleCardSize = singleCardOptimalSizes.length > 0 
        ? Math.min(...singleCardOptimalSizes) 
        : 7; // fallback size

    console.log(`Single cards unified font size: ${minSingleCardSize.toFixed(2)}pt`);

    // Second pass: apply sizes
    sortedCards.forEach(card => {
        if (card.classList.contains('card-single')) {
            applyFontSizeToCard(card, minSingleCardSize);
            
            const body = card.querySelector('.card-body');
            const cardType = 'single';
            console.log(`→ ${cardType} card final font ${minSingleCardSize.toFixed(2)}pt ${isOverflowing(body) ? '(OVERFLOWING!)' : ''}`);
        } else {
            // For multi-cards, use individual sizing as before
            const optimalSize = calculateOptimalFontSize(card);
            if (optimalSize !== null) {
                applyFontSizeToCard(card, optimalSize);
                
                const body = card.querySelector('.card-content');
                const cardType = card.classList.contains('card-double') ? 'double' : 'triple';
                console.log(`→ ${cardType} card final font ${optimalSize.toFixed(2)}pt ${isOverflowing(body) ? '(OVERFLOWING!)' : ''}`);
            }
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