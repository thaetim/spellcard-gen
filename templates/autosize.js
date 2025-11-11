/* -------------------------------------------------------------
   Auto-size card title with smart line breaking
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
function calculateOptimalFontSizePx(card, textEl, containerEl, header, footer, attrs, attrInfo, isWideCard = false, attempt = 0) {
    const minFont = { single: 11, double: 9, triple: 9 };
    const maxFont = { single: 14, double: 11, triple: 10 };
    const MAX_ATTEMPTS = 10;

    let cardType = 'single';
    if (card.classList.contains('card-wide-2')) cardType = 'double';
    if (card.classList.contains('card-wide-3')) cardType = 'triple';

    const minSize = minFont[cardType];
    const maxSize = maxFont[cardType];
    let fontSize = maxSize;

    const lineHeightFor = size => 1 + 0.05 * (size - minSize);

    textEl.style.cssText = `font-size: ${fontSize}px; line-height: ${lineHeightFor(fontSize)}; white-space: normal;`;

    const containerRect = containerEl.getBoundingClientRect();
    const headerH = header?.getBoundingClientRect().height || 0;
    const footerH = footer?.getBoundingClientRect().height || 0;
    const attrsH = attrs?.getBoundingClientRect().height || 0;
    const attrInfoH = attrInfo?.getBoundingClientRect().height || 0;

    let availableHeight = containerRect.height - headerH - footerH - attrsH - attrInfoH;
    const style = getComputedStyle(containerEl);
    if (!isWideCard) {
        availableHeight -= (parseFloat(style.paddingTop) || 0) + (parseFloat(style.paddingBottom) || 0);
    }
    availableHeight = Math.max(availableHeight - 4, 0);

    if ((availableHeight < 20 || !Number.isFinite(availableHeight)) && attempt < MAX_ATTEMPTS) {
        console.warn(`Layout not ready (${availableHeight.toFixed(1)}px) for ${card.className}, retry ${attempt + 1}/${MAX_ATTEMPTS}`);
        setTimeout(() => calculateOptimalFontSizePx(card, textEl, containerEl, header, footer, attrs, attrInfo, isWideCard, attempt + 1), 300);
        return fontSize;
    } else if (attempt >= MAX_ATTEMPTS) {
        console.warn(`Aborting layout retries for ${card.className} (stuck height: ${availableHeight.toFixed(1)}px)`);
    }

    const effectiveHeight = isWideCard ? availableHeight * 0.85 : availableHeight;
    const scrollH = textEl.scrollHeight;

    if (scrollH <= effectiveHeight * 0.98) {
        while (textEl.scrollHeight < effectiveHeight * 0.8 && fontSize < maxSize) {
            fontSize += 0.2;
            textEl.style.fontSize = `${fontSize}px`;
            textEl.style.lineHeight = lineHeightFor(fontSize);
        }
        console.log(`✅ Card OK (${card.className}): font enlarged to ${fontSize.toFixed(2)}px`);
        return fontSize;
    }

    console.group(`Card font calc: ${card.className}`);
    console.log({ cardType, effectiveHeight, attrsH, attrInfoH, scrollH });

    let low = minSize, high = fontSize, optimal = fontSize, iter = 0;
    while (low <= high && iter < 40) {
        const mid = (low + high) / 2;
        textEl.style.fontSize = `${mid}px`;
        textEl.style.lineHeight = lineHeightFor(mid);
        const scroll = textEl.scrollHeight;
        if (scroll <= effectiveHeight) {
            optimal = mid;
            low = mid + 0.1;
        } else {
            high = mid - 0.1;
        }
        iter++;
    }

    optimal = Math.max(minSize, Math.min(maxSize, optimal));
    textEl.style.fontSize = `${optimal}px`;
    textEl.style.lineHeight = lineHeightFor(optimal);
    console.log(`✅ Final font size: ${optimal.toFixed(2)}px`);
    console.groupEnd();

    return optimal;
}

/* -------------------------------------------------------------
   Debug + fix overflow
   ------------------------------------------------------------- */
function debugAndFixOverflowPx(selector = ".card-text") {
    const elements = document.querySelectorAll(selector);
    const stats = { single: [], double: [], triple: [] };

    elements.forEach(el => {
        const card = el.closest(".card");
        if (!card) return;

        let cardType = 'single';
        if (card.classList.contains('card-wide-2')) cardType = 'double';
        if (card.classList.contains('card-wide-3')) cardType = 'triple';

        const rect = el.getBoundingClientRect();
        let font = parseFloat(window.getComputedStyle(el).fontSize);
        stats[cardType].push({ font, scrollH: el.scrollHeight, clientH: rect.height });

        // Correct any overflow if needed
        if (el.scrollHeight > rect.height || el.scrollWidth > rect.width) {
            let size = font;
            let safety = 0;
            while ((el.scrollHeight > rect.height || el.scrollWidth > rect.width) && size > 7 && safety < 50) {
                size -= 0.2;
                el.style.fontSize = `${size}px`;
                safety++;
            }
        }
    });

    // Log stats per card type
    for (const type of ['single', 'double', 'triple']) {
        const arr = stats[type];
        if (arr.length) {
            const fonts = arr.map(a => a.font);
            const minF = Math.min(...fonts);
            const maxF = Math.max(...fonts);
            const avgF = fonts.reduce((a,b)=>a+b,0)/fonts.length;
            console.log(`Font stats for ${type} cards: count=${arr.length}, min=${minF.toFixed(2)}px, avg=${avgF.toFixed(2)}px, max=${maxF.toFixed(2)}px`);
        }
    }
}

/* -------------------------------------------------------------
   Auto-size card text (integrated)
   ------------------------------------------------------------- */
function autoSizeCardTextPx() {
    const singleCards = document.querySelectorAll('.card-single');
    singleCards.forEach(card => {
        const textEl = card.querySelector('.card-text');
        const bodyEl = card.querySelector('.card-body');
        if (!textEl || !bodyEl) return;
        const header = card.querySelector('.card-header');
        const footer = card.querySelector('.card-footer');
        const attrs = bodyEl.querySelector('.card-attrs');
        const attrInfo = bodyEl.querySelector('.card-attr-info');
        calculateOptimalFontSizePx(card, textEl, bodyEl, header, footer, attrs, attrInfo, false);
    });

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
            calculateOptimalFontSizePx(card, textEl, contentEl, header, footer, attrs, attrInfo, true);
        }
    });

    debugAndFixOverflowPx(".card-text");
}

/* -------------------------------------------------------------
   Layout stability helper
   ------------------------------------------------------------- */
function waitForLayoutStable(callback, interval = 200, stableCount = 3) {
    let lastSum = 0, stable = 0;
    const cardTexts = document.querySelectorAll('.card-text');
    const timer = setInterval(() => {
        let total = 0;
        for (let i = 0; i < cardTexts.length; i++) total += cardTexts[i].scrollHeight;
        if (total === lastSum) stable++; else { stable = 0; lastSum = total; }
        if (stable >= stableCount) { clearInterval(timer); callback(); }
    }, interval);
}

/* -------------------------------------------------------------
   Throttled resize handler
   ------------------------------------------------------------- */
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments, context = this;
        if (!inThrottle) { func.apply(context, args); inThrottle = true; setTimeout(() => inThrottle = false, limit); }
    }
}

/* -------------------------------------------------------------
   Run everything on load and resize
   ------------------------------------------------------------- */
const autoSizeAll = throttle(() => {
    autoSizeCardTitle();
    autoSizeCardTextPx();
}, 100);

document.addEventListener('DOMContentLoaded', () => {
    autoSizeAll();
    waitForLayoutStable(() => { console.log('Layout stabilized — final sizing pass'); autoSizeAll(); });
    const mo = new MutationObserver(() => debugAndFixOverflowPx(".card-text"));
    mo.observe(document.body, { childList: true, subtree: true });
});

window.addEventListener('resize', autoSizeAll);
