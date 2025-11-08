/* -------------------------------------------------------------
   Auto‑size card title with smart line breaking
   ------------------------------------------------------------- */
function autoSizeCardTitle() {
    const cards = document.querySelectorAll('.card');

    cards.forEach(card => {
        const title = card.querySelector('.card-title');
        if (!title) return;

        const originalText = title.textContent;
        let fontSize = 17;               // pt
        const minSize = 15;
        title.style.fontSize = fontSize + 'pt';
        title.style.lineHeight = '1.1';
        title.style.overflow = 'hidden';
        void title.offsetHeight;          // force layout

        const isMultiline = () => {
            const origWS = title.style.whiteSpace;
            title.style.whiteSpace = 'nowrap';
            void title.offsetHeight;
            const single = title.offsetHeight;
            title.style.whiteSpace = origWS;
            void title.offsetHeight;
            const current = title.offsetHeight;
            return current > single * 1.5;
        };

        let multiline = isMultiline();
        
        // Try smart line breaking before shrinking
        if (multiline && fontSize === 17) {
            const breakWords = ['\nof', ' of ', ' and ', ' or ', ' at ', ' to ', ' in ', ' the '];
            let bestBreak = null;
            let bestScore = Infinity;
            
            for (const breakWord of breakWords) {
                const searchText = breakWord.startsWith('\n') 
                    ? breakWord.substring(1) // Search for 'of' when looking for '\nof'
                    : breakWord;
                const idx = originalText.toLowerCase().indexOf(searchText);
                if (idx > 0) {
                    // Score based on how close to middle
                    const mid = originalText.length / 2;
                    const score = Math.abs((idx + searchText.length / 2) - mid);
                    if (score < bestScore) {
                        bestScore = score;
                        // For \nof pattern, break before 'of'
                        bestBreak = breakWord.startsWith('\n') ? idx : idx + searchText.length;
                    }
                }
            }
            
            if (bestBreak) {
                title.innerHTML = originalText.substring(0, bestBreak).trim() + '<br>' + 
                                 originalText.substring(bestBreak).trim();
                void title.offsetHeight;
                multiline = isMultiline();
            }
        }

        while (multiline && fontSize > minSize) {
            fontSize -= 0.1;
            title.style.fontSize = fontSize + 'pt';
            void title.offsetHeight;
            multiline = isMultiline();
        }
    });
}

/* -------------------------------------------------------------
   Calculate optimal font size for a card's text
   ------------------------------------------------------------- */
function calculateOptimalFontSize(card, textEl, bodyEl, header, footer, attrs, attrInfo, isContinuation) {
    const minSize = 4;
    const maxSize = 10;
    let fontSize = 9;  // Start at a reasonable middle value
    
    /* ---- linear line‑height function ---- */
    const lineHeightFor = size => {
        const maxSizeL = 15;
        const minSizeL = 4;
        const maxLH = 1.2, minLH = 0.9;
        const t = (size - minSizeL) / (maxSizeL - minSizeL);
        return minLH + t * (maxLH - minLH);
    };
    
    textEl.style.fontSize   = fontSize + 'pt';
    textEl.style.lineHeight = lineHeightFor(fontSize);
    
    /* ---- compute available height ---- */
    const cardHeight   = card.offsetHeight;
    const headerH      = header ? header.offsetHeight : 0;
    const footerH      = footer ? footer.offsetHeight + 1 : 0;
    const attrsH       = attrs ? attrs.offsetHeight : 0;
    const attrInfoH    = attrInfo ? attrInfo.offsetHeight : 0;
    const bodyPad      = isContinuation ? 5 : 4;
    const textMargin   = 3;
    const safetyMargin = 2;
    
    const availableHeight = cardHeight - headerH - footerH
                           - attrsH - attrInfoH
                           - bodyPad - textMargin - 5 - safetyMargin;
    
    /* ---- Try to grow to fill space ---- */
    while (textEl.scrollHeight < availableHeight * 0.95 && fontSize < maxSize) {
        fontSize += 0.1;
        textEl.style.fontSize   = fontSize + 'pt';
        textEl.style.lineHeight = lineHeightFor(fontSize);
        void textEl.offsetHeight;
    }
    
    /* ---- Shrink if overflowed ---- */
    while (textEl.scrollHeight > availableHeight && fontSize > minSize) {
        fontSize -= 0.05;
        textEl.style.fontSize   = fontSize + 'pt';
        textEl.style.lineHeight = lineHeightFor(fontSize);
        void textEl.offsetHeight;
    }
    
    return fontSize;
}

/* -------------------------------------------------------------
   Enhanced auto‑size for the description text
   ------------------------------------------------------------- */
function autoSizeCardText() {
    const cards = document.querySelectorAll('.card');
    
    // Group cards by their base ID (to pair continuation cards with their originals)
    const cardPairs = new Map();
    
    cards.forEach(card => {
        const cardId = card.id;
        if (!cardId) return;
        
        const isContinuation = cardId.endsWith('-cont');
        const baseId = isContinuation ? cardId.replace('-cont', '') : cardId;
        
        if (!cardPairs.has(baseId)) {
            cardPairs.set(baseId, { original: null, continuation: null });
        }
        
        if (isContinuation) {
            cardPairs.get(baseId).continuation = card;
        } else {
            cardPairs.get(baseId).original = card;
        }
    });
    
    // Process each pair
    cardPairs.forEach((pair, baseId) => {
        const { original, continuation } = pair;
        
        // If there's only one card (no split), process normally
        if (!continuation && original) {
            const textEl   = original.querySelector('.card-text');
            const bodyEl   = original.querySelector('.card-body');
            const header   = original.querySelector('.card-header');
            const footer   = original.querySelector('.card-footer');
            const attrs    = bodyEl?.querySelector('.card-attrs');
            const attrInfo = bodyEl?.querySelector('.card-attr-info');
            
            if (textEl && bodyEl) {
                calculateOptimalFontSize(original, textEl, bodyEl, header, footer, attrs, attrInfo, false);
            }
            return;
        }
        
        // If we have both parts, calculate optimal size for both and use the smaller
        if (original && continuation) {
            const origTextEl   = original.querySelector('.card-text');
            const origBodyEl   = original.querySelector('.card-body');
            const origHeader   = original.querySelector('.card-header');
            const origFooter   = original.querySelector('.card-footer');
            const origAttrs    = origBodyEl?.querySelector('.card-attrs');
            const origAttrInfo = origBodyEl?.querySelector('.card-attr-info');
            
            const contTextEl   = continuation.querySelector('.card-text');
            const contBodyEl   = continuation.querySelector('.card-body');
            const contHeader   = continuation.querySelector('.card-header');
            const contFooter   = continuation.querySelector('.card-footer');
            const contAttrs    = contBodyEl?.querySelector('.card-attrs');
            const contAttrInfo = contBodyEl?.querySelector('.card-attr-info');
            
            if (origTextEl && origBodyEl && contTextEl && contBodyEl) {
                // Calculate optimal size for each part
                const origSize = calculateOptimalFontSize(
                    original, origTextEl, origBodyEl, origHeader, origFooter, origAttrs, origAttrInfo, false
                );
                
                const contSize = calculateOptimalFontSize(
                    continuation, contTextEl, contBodyEl, contHeader, contFooter, contAttrs, contAttrInfo, true
                );
                
                // Use the smaller of the two sizes for both cards
                const finalSize = Math.min(origSize, contSize);
                
                const lineHeightFor = size => {
                    const maxSizeL = 15, minSizeL = 4;
                    const maxLH = 1.2, minLH = 0.9;
                    const t = (size - minSizeL) / (maxSizeL - minSizeL);
                    return minLH + t * (maxLH - minLH);
                };
                
                // Apply the final size to both cards
                origTextEl.style.fontSize = finalSize + 'pt';
                origTextEl.style.lineHeight = lineHeightFor(finalSize);
                
                contTextEl.style.fontSize = finalSize + 'pt';
                contTextEl.style.lineHeight = lineHeightFor(finalSize);
            }
        }
    });
}

/* -------------------------------------------------------------
   Helper: wait until layout stops changing (your original version)
   ------------------------------------------------------------- */
function waitForLayoutStable(callback, interval = 200, stableCount = 3) {
    let lastSum = 0, stable = 0;
    const timer = setInterval(() => {
        const total = [...document.querySelectorAll('.card-text')]
            .reduce((sum, el) => sum + el.scrollHeight, 0);
        if (total === lastSum) {
            stable++;
        } else {
            stable = 0;
            lastSum = total;
        }
        if (stable >= stableCount) {
            clearInterval(timer);
            callback();
        }
    }, interval);
}

/* -------------------------------------------------------------
   Run everything on load, on resize, and after layout stabilises
   ------------------------------------------------------------- */
function autoSizeAll() {
    autoSizeCardTitle();
    autoSizeCardText();
}

document.addEventListener('DOMContentLoaded', () => {
    autoSizeAll();                     // first pass
    waitForLayoutStable(() => {
        console.log('Layout stabilized — final autoSizeAll()');
        autoSizeAll();                 // final pass after any async content
    });
});

window.addEventListener('resize', autoSizeAll);
