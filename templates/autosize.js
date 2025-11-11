/* -------------------------------------------------------------
   Throttled function wrapper
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
   Wait for layout to stabilize
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
   Auto-size card title with smart line breaking
   ------------------------------------------------------------- */
function autoSizeCardTitle() {
    const cards = document.querySelectorAll('.card-single, .card-wide');
    const breakWords = ['\nof', ' of ', ' and ', ' or ', ' at ', ' to ', ' in ', ' the '];
    const minSize = 15;
    const lineHeight = '1.1';
    const overflow = 'hidden';

    cards.forEach(card => {
        const title = card.querySelector('.card-header .card-title');
        if (!title) return;

        const originalText = title.textContent;
        let fontSize = 17;

        title.style.cssText = `font-size: ${fontSize}pt; line-height: ${lineHeight}; overflow: ${overflow};`;
        const titleRect = title.getBoundingClientRect();

        const isMultiline = (() => {
            const origWS = title.style.whiteSpace;
            title.style.whiteSpace = 'nowrap';
            const singleLineHeight = title.getBoundingClientRect().height;
            title.style.whiteSpace = origWS;
            const currentHeight = title.getBoundingClientRect().height;
            return currentHeight > singleLineHeight * 1.5;
        })();

        let multiline = isMultiline;

        if (multiline && fontSize === 17) {
            let bestBreak = null;
            let bestScore = Infinity;
            const textLower = originalText.toLowerCase();
            const mid = originalText.length / 2;

            for (const breakWord of breakWords) {
                const searchText = breakWord.startsWith('\n') ? breakWord.substring(1) : breakWord;
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

        if (multiline && fontSize > minSize) {
            let low = minSize, high = fontSize, optimalSize = minSize;
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
   Calculate optimal font size for card text (in pt)
   ------------------------------------------------------------- */
function calculateOptimalFontSize(card, textEl, containerEl, header, footer, attrs, attrInfo, isWideCard = false, attempt = 0) {
    const minFont = { single: 8, double: 8, triple: 8 };
    const maxFont = { single: 10, double: 10, triple: 10 };
    const MAX_ATTEMPTS = 42;

    let cardType = 'single';
    if (card.classList.contains('card-wide-2')) cardType = 'double';
    if (card.classList.contains('card-wide-3')) cardType = 'triple';

    const minSize = minFont[cardType];
    const maxSize = maxFont[cardType];
    let fontSize = maxSize;

    const lineHeightFor = size => 1 + 0.05 * (size - minSize);

    textEl.style.cssText = `font-size: ${fontSize}pt; line-height: ${lineHeightFor(fontSize)}; white-space: normal;`;

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
        setTimeout(() => calculateOptimalFontSize(card, textEl, containerEl, header, footer, attrs, attrInfo, isWideCard, attempt + 1), 300);
        return fontSize;
    }

    const effectiveHeight = isWideCard ? availableHeight * 0.85 : availableHeight;

    // Step 1: Shrink font if overflow
    while (textEl.scrollHeight > effectiveHeight && fontSize > minSize) {
        fontSize -= 0.2;
        textEl.style.fontSize = `${fontSize}pt`;
        textEl.style.lineHeight = lineHeightFor(fontSize);
    }

    // Step 2: Grow slightly if there’s space
    while (textEl.scrollHeight < effectiveHeight * 0.9 && fontSize < maxSize) {
        fontSize += 0.2;
        textEl.style.fontSize = `${fontSize}pt`;
        textEl.style.lineHeight = lineHeightFor(fontSize);
    }

    return fontSize;
}

/* -------------------------------------------------------------
   Debug + fix overflow
   ------------------------------------------------------------- */
function debugAndFixOverflow(selector = ".card-text") {
    const elements = document.querySelectorAll(selector);
    console.log('Cards found:', elements.length)
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

        // Correct overflow
        if (el.scrollHeight > rect.height || el.scrollWidth > rect.width) {
            let size = font, safety = 0;
            while ((el.scrollHeight > rect.height || el.scrollWidth > rect.width) && size > 7 && safety < 50) {
                size -= 0.2;
                el.style.fontSize = `${size}pt`;
                safety++;
            }
        }
    });

    for (const type of ['single', 'double', 'triple']) {
        const arr = stats[type];
        if (arr.length) {
            const fonts = arr.map(a => a.font);
            const minF = Math.min(...fonts);
            const maxF = Math.max(...fonts);
            const avgF = fonts.reduce((a,b)=>a+b,0)/fonts.length;
            console.log(`Font stats for ${type} cards: count=${arr.length}, min=${minF.toFixed(2)}pt, avg=${avgF.toFixed(2)}pt, max=${maxF.toFixed(2)}pt`);
        }
    }
}

/* -------------------------------------------------------------
   Auto-size card text (integrated)
   ------------------------------------------------------------- */
function autoSizeCardText() {
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

    debugAndFixOverflow(".card-text");
}

/* -------------------------------------------------------------
   Run everything on load and resize
   ------------------------------------------------------------- */
const autoSizeAll = throttle(() => {
    autoSizeCardTitle();
    autoSizeCardText();
}, 100);

document.addEventListener('DOMContentLoaded', () => {
    autoSizeAll();
    setTimeout(() => {
        debugAndFixOverflow(".card-text");
    }, 100);
    waitForLayoutStable(() => { 
        console.log('Layout stabilized — final sizing pass'); 
        autoSizeAll(); 
        debugAndFixOverflow(".card-text");
    });
});

window.addEventListener('resize', autoSizeAll);


