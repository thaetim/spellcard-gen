/* -------------------------------------------------------------
   Auto‑size card title with smart line breaking
   ------------------------------------------------------------- */
function autoSizeCardTitle() {
    const cards = document.querySelectorAll('.card-single, .card-wide');
    const breakWords = ['\nof', ' of ', ' and ', ' or ', ' at ', ' to ', ' in ', ' the '];
    
    // Pre-calculate reusable values
    const minSize = 15;
    const lineHeight = '1.1';
    const overflow = 'hidden';

    cards.forEach(card => {
        const title = card.querySelector('.card-header .card-title');
        if (!title) return;

        const originalText = title.textContent;
        let fontSize = 17;
        
        // Batch style changes to minimize reflows
        title.style.cssText = `font-size: ${fontSize}pt; line-height: ${lineHeight}; overflow: ${overflow};`;
        
        // Single forced layout
        const titleRect = title.getBoundingClientRect();
        
        // Optimized multiline check with cached measurements
        const isMultiline = (() => {
            const origWS = title.style.whiteSpace;
            title.style.whiteSpace = 'nowrap';
            const singleLineHeight = title.getBoundingClientRect().height;
            title.style.whiteSpace = origWS;
            const currentHeight = title.getBoundingClientRect().height;
            return currentHeight > singleLineHeight * 1.5;
        })();

        let multiline = isMultiline;
        
        // Smart line breaking optimization
        if (multiline && fontSize === 17) {
            let bestBreak = null;
            let bestScore = Infinity;
            const textLower = originalText.toLowerCase();
            const mid = originalText.length / 2;
            
            for (const breakWord of breakWords) {
                const searchText = breakWord.startsWith('\n') 
                    ? breakWord.substring(1) 
                    : breakWord;
                const idx = textLower.indexOf(searchText);
                
                if (idx > 0) {
                    const score = Math.abs((idx + searchText.length / 2) - mid);
                    if (score < bestScore) {
                        bestScore = score;
                        bestBreak = breakWord.startsWith('\n') ? idx : idx + searchText.length;
                    }
                }
            }
            
            if (bestBreak) {
                title.innerHTML = originalText.substring(0, bestBreak).trim() + '<br>' + 
                                 originalText.substring(bestBreak).trim();
                multiline = title.scrollHeight > titleRect.height * 1.5;
            }
        }

        // Optimized font size reduction with binary search approach
        if (multiline && fontSize > minSize) {
            let low = minSize;
            let high = fontSize;
            let optimalSize = minSize;
            
            // Binary search for optimal font size
            while (low <= high) {
                const midSize = (low + high) / 2;
                title.style.fontSize = midSize + 'pt';
                
                if (title.scrollHeight <= titleRect.height * 1.5) {
                    optimalSize = midSize;
                    low = midSize + 0.1;
                } else {
                    high = midSize - 0.1;
                }
            }
            
            title.style.fontSize = optimalSize + 'pt';
        }
    });
}

/* -------------------------------------------------------------
   Calculate optimal font size for a card's text
   ------------------------------------------------------------- */
function calculateOptimalFontSize(card, textEl, containerEl, header, footer, attrs, attrInfo, isWideCard = false) {
    const minSize = 6;      // bump up safety min
    const maxSize = 10;
    let fontSize = 9;

    const lineHeightFor = size => {
        const maxSizeL = 15, minSizeL = 4;
        const maxLH = 1.2, minLH = 0.9;
        const t = (size - minSizeL) / (maxSizeL - minSizeL);
        return minLH + t * (maxLH - minLH);
    };

    // Reset to baseline before measuring
    textEl.style.cssText = `font-size: ${fontSize}pt; line-height: ${lineHeightFor(fontSize)}; white-space: normal;`;

    const cardRect = card.getBoundingClientRect();
    const containerRect = containerEl.getBoundingClientRect();
    const headerH = header?.getBoundingClientRect().height || 0;
    const footerH = footer?.getBoundingClientRect().height || 0;
    const attrsH = attrs?.getBoundingClientRect().height || 0;
    const attrInfoH = attrInfo?.getBoundingClientRect().height || 0;

    // Defensive height computation
    let availableHeight = containerRect.height - attrsH - attrInfoH;
    if (!isWideCard) availableHeight -= (parseFloat(getComputedStyle(containerEl).paddingTop) || 0)
                                       + (parseFloat(getComputedStyle(containerEl).paddingBottom) || 0);
    availableHeight -= 6; // safety margin

    // Fallback: if layout not ready (zero/invalid)
    if (availableHeight < 80 || !Number.isFinite(availableHeight)) {
        console.warn('Layout not ready, retrying later...', availableHeight);
        setTimeout(() => calculateOptimalFontSize(card, textEl, containerEl, header, footer, attrs, attrInfo, isWideCard), 500);
        return fontSize;
    }

    const effectiveHeight = isWideCard ? availableHeight * 0.85 : availableHeight;

    // Early exit: if text already fits comfortably, skip binary shrink
    if (textEl.scrollHeight <= effectiveHeight * 0.95) {
        // restore baseline if too small
        textEl.style.fontSize = fontSize + 'pt';
        return fontSize;
    }

    // Binary search shrinker
    let low = minSize, high = maxSize, optimal = fontSize;
    while (low <= high && Math.abs(high - low) > 0.05) {
        const mid = (low + high) / 2;
        const lh = lineHeightFor(mid);
        textEl.style.cssText = `font-size: ${mid}pt; line-height: ${lh}; white-space: normal;`;
        if (textEl.scrollHeight <= effectiveHeight) {
            optimal = mid;
            low = mid + 0.05;
        } else {
            high = mid - 0.05;
        }
    }

    // Final clamp and style
    optimal = Math.max(minSize, Math.min(maxSize, optimal));
    const finalLH = lineHeightFor(optimal);
    textEl.style.cssText = `font-size: ${optimal}pt; line-height: ${finalLH}; white-space: normal;`;

    console.log(`Card: ${card.className}, Final font: ${optimal.toFixed(2)}pt, avail=${availableHeight.toFixed(1)}px, used=${textEl.scrollHeight.toFixed(1)}px`);
    return optimal;
}

/* -------------------------------------------------------------
   Enhanced auto‑size for the description text
   ------------------------------------------------------------- */
function autoSizeCardText() {
    // Process single cards
    const singleCards = document.querySelectorAll('.card-single');
    singleCards.forEach(card => {
        const textEl = card.querySelector('.card-text');
        const bodyEl = card.querySelector('.card-body');
        if (!textEl || !bodyEl) return;
        
        const header = card.querySelector('.card-header');
        const footer = card.querySelector('.card-footer');
        const attrs = bodyEl.querySelector('.card-attrs');
        const attrInfo = bodyEl.querySelector('.card-attr-info');
        
        calculateOptimalFontSize(card, textEl, bodyEl, header, footer, attrs, attrInfo, false);
    });
    
    // Process wide cards
    const wideCards = document.querySelectorAll('.card-wide');
    wideCards.forEach(card => {
        const isDouble = card.classList.contains('card-wide-2');
        const isTriple = card.classList.contains('card-wide-3');
        
        if (isDouble || isTriple) {
            const contentEl = card.querySelector('.card-content');
            const textEl = contentEl.querySelector('.card-text');
            if (!textEl) return;
            
            const header = card.querySelector('.card-header-group');
            const footer = card.querySelector('.card-footer-group');
            const attrs = contentEl.querySelector('.card-attrs');
            const attrInfo = contentEl.querySelector('.card-attr-info');
            
            calculateOptimalFontSize(card, textEl, contentEl, header, footer, attrs, attrInfo, true);
        }
    });
}

/* -------------------------------------------------------------
   Optimized layout stability helper
   ------------------------------------------------------------- */
function waitForLayoutStable(callback, interval = 200, stableCount = 3) {
    let lastSum = 0, stable = 0;
    const cardTexts = document.querySelectorAll('.card-text');
    
    const timer = setInterval(() => {
        let total = 0;
        for (let i = 0; i < cardTexts.length; i++) {
            total += cardTexts[i].scrollHeight;
        }
        
        if (total === lastSum) {
            stable++;
            if (stable >= stableCount) {
                clearInterval(timer);
                callback();
            }
        } else {
            stable = 0;
            lastSum = total;
        }
    }, interval);
}

/* -------------------------------------------------------------
   Throttled resize handler
   ------------------------------------------------------------- */
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

/* -------------------------------------------------------------
   Run everything on load, on resize, and after layout stabilises
   ------------------------------------------------------------- */
const autoSizeAll = throttle(() => {
    autoSizeCardTitle();
    autoSizeCardText();
}, 100);

document.addEventListener('DOMContentLoaded', () => {
    autoSizeAll();
    waitForLayoutStable(() => {
        console.log('Layout stabilized — final autoSizeAll()');
        autoSizeAll();
    });
});

window.addEventListener('resize', autoSizeAll);