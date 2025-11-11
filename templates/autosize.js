/* -------------------------------------------------------------
   Auto‑size card title with smart line breaking
   ------------------------------------------------------------- */
function autoSizeCardTitle() {
    const cards = document.querySelectorAll('.card');
    const breakWords = ['\nof', ' of ', ' and ', ' or ', ' at ', ' to ', ' in ', ' the '];
    
    // Pre-calculate reusable values
    const minSize = 15;
    const lineHeight = '1.1';
    const overflow = 'hidden';

    cards.forEach(card => {
        const title = card.querySelector('.card-title');
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
function calculateOptimalFontSize(card, textEl, bodyEl, header, footer, attrs, attrInfo, isContinuation) {
    const minSize = 4;
    const maxSize = 10;
    let fontSize = 9;
    
    // Pre-calculate line height function
    const lineHeightFor = size => {
        const maxSizeL = 15;
        const minSizeL = 4;
        const maxLH = 1.2, minLH = 0.9;
        const t = (size - minSizeL) / (maxSizeL - minSizeL);
        return minLH + t * (maxLH - minLH);
    };
    
    // Batch style application
    const lineHeight = lineHeightFor(fontSize);
    textEl.style.cssText = `font-size: ${fontSize}pt; line-height: ${lineHeight};`;
    
    // Single measurement pass for all heights
    const cardHeight = card.offsetHeight;
    const headerH = header ? header.offsetHeight : 0;
    const footerH = footer ? footer.offsetHeight + 1 : 0;
    const attrsH = attrs ? attrs.offsetHeight : 0;
    const attrInfoH = attrInfo ? attrInfo.offsetHeight : 0;
    const bodyPad = isContinuation ? 5 : 4;
    const textMargin = 3;
    const safetyMargin = 2;
    
    const availableHeight = cardHeight - headerH - footerH - attrsH - attrInfoH - bodyPad - textMargin - 5 - safetyMargin;
    
    // Optimized size adjustment with binary search
    let low = minSize;
    let high = maxSize;
    let optimalSize = fontSize;
    
    while (low <= high && Math.abs(high - low) > 0.05) {
        const midSize = (low + high) / 2;
        const currentLineHeight = lineHeightFor(midSize);
        textEl.style.cssText = `font-size: ${midSize}pt; line-height: ${currentLineHeight};`;
        
        if (textEl.scrollHeight <= availableHeight) {
            optimalSize = midSize;
            low = midSize + 0.05;
        } else {
            high = midSize - 0.05;
        }
    }
    
    // Apply final optimal size
    const finalLineHeight = lineHeightFor(optimalSize);
    textEl.style.cssText = `font-size: ${optimalSize}pt; line-height: ${finalLineHeight};`;
    
    return optimalSize;
}

/* -------------------------------------------------------------
   Enhanced auto‑size for the description text
   ------------------------------------------------------------- */
function autoSizeCardText() {
    const cards = document.querySelectorAll('.card');
    const cardPairs = new Map();
    
    // Single pass to group cards (including wide cards)
    cards.forEach(card => {
        const cardId = card.id;
        if (!cardId) return;
        
        // Handle wide cards (card-wide-first + card-wide-cont)
        if (card.classList.contains('card-wide-first')) {
            const baseId = cardId;
            const cont2 = document.getElementById(`${baseId}-cont2`);
            const cont3 = document.getElementById(`${baseId}-cont3`);
            
            if (cont3) {
                processWideCardTriple(card, cont2, cont3);
            } else if (cont2) {
                processWideCardDouble(card, cont2);
            }
            return;
        }
        
        // Skip if already processed as part of wide card
        if (card.classList.contains('card-wide-cont')) return;
        
        const isContinuation = cardId.endsWith('-cont');
        const baseId = isContinuation ? cardId.replace('-cont', '') : cardId;
        
        if (!cardPairs.has(baseId)) {
            cardPairs.set(baseId, { original: null, continuation: null });
        }
        
        const pair = cardPairs.get(baseId);
        if (isContinuation) {
            pair.continuation = card;
        } else {
            pair.original = card;
        }
    });
    
    // Process pairs with cached queries
    cardPairs.forEach((pair, baseId) => {
        const { original, continuation } = pair;
        
        if (!continuation && original) {
            processSingleCard(original, false);
            return;
        }
        
        if (original && continuation) {
            processCardPair(original, continuation);
        }
    });
    
    function processSingleCard(card, isContinuation) {
        const textEl = card.querySelector('.card-text');
        const bodyEl = card.querySelector('.card-body');
        if (!textEl || !bodyEl) return;
        
        const header = card.querySelector('.card-header');
        const footer = card.querySelector('.card-footer');
        const attrs = bodyEl.querySelector('.card-attrs');
        const attrInfo = bodyEl.querySelector('.card-attr-info');
        
        calculateOptimalFontSize(card, textEl, bodyEl, header, footer, attrs, attrInfo, isContinuation);
    }
    
    function processCardPair(original, continuation) {
        const origTextEl = original.querySelector('.card-text');
        const origBodyEl = original.querySelector('.card-body');
        const contTextEl = continuation.querySelector('.card-text');
        const contBodyEl = continuation.querySelector('.card-body');
        
        if (!origTextEl || !origBodyEl || !contTextEl || !contBodyEl) return;
        
        // Single query for all elements
        const origHeader = original.querySelector('.card-header');
        const origFooter = original.querySelector('.card-footer');
        const origAttrs = origBodyEl.querySelector('.card-attrs');
        const origAttrInfo = origBodyEl.querySelector('.card-attr-info');
        
        const contHeader = continuation.querySelector('.card-header');
        const contFooter = continuation.querySelector('.card-footer');
        const contAttrs = contBodyEl.querySelector('.card-attrs');
        const contAttrInfo = contBodyEl.querySelector('.card-attr-info');
        
        // Helper function for line height calculation
        const lineHeightFor = size => {
            const maxSizeL = 15;
            const minSizeL = 4;
            const maxLH = 1.2, minLH = 0.9;
            const t = (size - minSizeL) / (maxSizeL - minSizeL);
            return minLH + t * (maxLH - minLH);
        };
        
        const origSize = calculateOptimalFontSize(
            original, origTextEl, origBodyEl, origHeader, origFooter, origAttrs, origAttrInfo, false
        );
        
        const contSize = calculateOptimalFontSize(
            continuation, contTextEl, contBodyEl, contHeader, contFooter, contAttrs, contAttrInfo, true
        );
        
        const finalSize = Math.min(origSize, contSize);
        const finalLineHeight = lineHeightFor(finalSize);
        
        // Batch style updates
        origTextEl.style.cssText = `font-size: ${finalSize}pt; line-height: ${finalLineHeight};`;
        contTextEl.style.cssText = `font-size: ${finalSize}pt; line-height: ${finalLineHeight};`;
    }
    
    
    function processWideCardDouble(card1, card2) {
        const text1 = card1.querySelector('.card-text');
        if (!text1) return;
        
        const body1 = card1.querySelector('.card-body');
        
        // Helper function for line height calculation
        const lineHeightFor = size => {
            const maxSizeL = 15;
            const minSizeL = 4;
            const maxLH = 1.2, minLH = 0.9;
            const t = (size - minSizeL) / (maxSizeL - minSizeL);
            return minLH + t * (maxLH - minLH);
        };
        
        // For wide cards, all text is in the first card split into columns
        // We need to account for the total height being spread across 2 columns
        const size1 = calculateOptimalFontSize(card1, text1, body1, 
            card1.querySelector('.card-header'),
            card1.querySelector('.card-footer'),
            body1.querySelector('.card-attrs'),
            body1.querySelector('.card-attr-info'), false);
        
        const finalLineHeight = lineHeightFor(size1);
        text1.style.cssText = `font-size: ${size1}pt; line-height: ${finalLineHeight};`;
    }
    
    function processWideCardTriple(card1, card2, card3) {
        const text1 = card1.querySelector('.card-text');
        if (!text1) return;
        
        const body1 = card1.querySelector('.card-body');
        
        // Helper function for line height calculation
        const lineHeightFor = size => {
            const maxSizeL = 15;
            const minSizeL = 4;
            const maxLH = 1.2, minLH = 0.9;
            const t = (size - minSizeL) / (maxSizeL - minSizeL);
            return minLH + t * (maxLH - minLH);
        };
        
        // For triple-wide cards, all text is in the first card split into 3 columns
        const size1 = calculateOptimalFontSize(card1, text1, body1,
            card1.querySelector('.card-header'),
            card1.querySelector('.card-footer'),
            body1.querySelector('.card-attrs'),
            body1.querySelector('.card-attr-info'), false);
        
        const finalLineHeight = lineHeightFor(size1);
        text1.style.cssText = `font-size: ${size1}pt; line-height: ${finalLineHeight};`;
    }
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