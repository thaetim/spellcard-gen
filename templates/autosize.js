/* -------------------------------------------------------------
   Auto-size card title with smart line breaking
   ------------------------------------------------------------- */
function autoSizeCardTitle() {
    const cards = document.querySelectorAll('.card-single, .card-wide');
    const breakWords = ['\nof', ' of ', ' and ', ' or ', ' at ', ' to ', ' in ', ' the '];
    
    const minSize = 15; // px
    const lineHeight = '1.1';
    const overflow = 'hidden';

    cards.forEach(card => {
        const title = card.querySelector('.card-header .card-title');
        if (!title) return;

        const originalText = title.textContent;
        let fontSize = 17;

        title.style.cssText = `font-size: ${fontSize}px; line-height: ${lineHeight}; overflow: ${overflow};`;
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

        if (multiline && fontSize > minSize) {
            let low = minSize, high = fontSize, optimalSize = minSize;
            while (low <= high) {
                const midSize = (low + high) / 2;
                title.style.fontSize = midSize + 'px';
                if (title.scrollHeight <= titleRect.height * 1.5) {
                    optimalSize = midSize;
                    low = midSize + 0.1;
                } else {
                    high = midSize - 0.1;
                }
            }
            title.style.fontSize = optimalSize + 'px';
        }
    });
}

/* -------------------------------------------------------------
   Diagnostic font stats storage
   ------------------------------------------------------------- */
const cardTypeStats = {
  single: [],
  double: [],
  triple: []
};

function logCardTypeStats() {
  Object.entries(cardTypeStats).forEach(([type, arr]) => {
    if (arr.length === 0) return;
    const min = Math.min(...arr.map(a => a.font));
    const max = Math.max(...arr.map(a => a.font));
    const avg = arr.reduce((s, a) => s + a.font, 0) / arr.length;

    console.group(`Font stats for ${type} cards`);
    console.log(`count=${arr.length}, min=${min.toFixed(2)}px, avg=${avg.toFixed(2)}px, max=${max.toFixed(2)}px`);
    const minCase = arr.find(a => a.font === min);
    const maxCase = arr.find(a => a.font === max);
    if (minCase) console.log('→ MIN case:', minCase.debug);
    if (maxCase) console.log('→ MAX case:', maxCase.debug);
    console.groupEnd();
  });
}

/* -------------------------------------------------------------
   Calculate optimal font size for card text (px units)
   ------------------------------------------------------------- */
function calculateOptimalFontSizePx(card, textEl, containerEl, header, footer, attrs, attrInfo, isWideCard = false) {
  const minSize = 8;
  const maxSize = 13;
  let fontSize = 11;

  const lineHeightFor = size => 1.05 + (size - minSize) * 0.015;

  textEl.style.fontSize = `${fontSize}px`;
  textEl.style.lineHeight = lineHeightFor(fontSize);
  textEl.style.whiteSpace = 'normal';

  const containerRect = containerEl.getBoundingClientRect();
  const headerH = header?.getBoundingClientRect().height || 0;
  const footerH = footer?.getBoundingClientRect().height || 0;
  const attrsH = attrs?.getBoundingClientRect().height || 0;
  const attrInfoH = attrInfo?.getBoundingClientRect().height || 0;

  let availableHeight = containerRect.height - headerH - footerH - attrsH - attrInfoH;
  const style = getComputedStyle(containerEl);
  availableHeight -= (parseFloat(style.paddingTop) || 0) + (parseFloat(style.paddingBottom) || 0);
  availableHeight = Math.max(availableHeight - 2, 0);
  const effectiveHeight = isWideCard ? availableHeight * 0.85 : availableHeight;

  // binary search shrink if overflow
  let low = minSize, high = fontSize, optimal = fontSize;
  let iter = 0;
  while (low <= high && iter < 40) {
    const mid = (low + high) / 2;
    textEl.style.fontSize = `${mid}px`;
    textEl.style.lineHeight = lineHeightFor(mid);
    if (textEl.scrollHeight <= effectiveHeight) {
      optimal = mid;
      low = mid + 0.1;
    } else {
      high = mid - 0.1;
    }
    iter++;
  }

  if (optimal < minSize + 0.5 && textEl.scrollHeight < effectiveHeight * 0.9)
    optimal = minSize + 0.5;

  textEl.style.fontSize = `${optimal}px`;
  textEl.style.lineHeight = lineHeightFor(optimal);

  const debugInfo = {
    font: optimal,
    effectiveHeight: effectiveHeight.toFixed(1),
    attrsH: attrsH.toFixed(1),
    attrInfoH: attrInfoH.toFixed(1),
    scrollH: textEl.scrollHeight,
    clientH: containerRect.height
  };

  const type =
    card.classList.contains('card-wide-3') ? 'triple' :
    card.classList.contains('card-wide-2') ? 'double' :
    'single';
  cardTypeStats[type].push({ font: optimal, debug: debugInfo });

  return optimal;
}

/* -------------------------------------------------------------
   Overflow-aware adjustment for fine-tuning
   ------------------------------------------------------------- */
function debugAndFixOverflow(selector = ".card-text") {
  document.querySelectorAll(selector).forEach((el, i) => {
    const card = el.closest(".card");
    const rect = el.getBoundingClientRect();
    const overflow = el.scrollHeight > rect.height + 1 || el.scrollWidth > rect.width + 1;

    console.group(`Overflow check ${i}: ${card?.className || '(no card)'}`);
    console.log(`scrollH=${el.scrollHeight}, clientH=${rect.height}, scrollW=${el.scrollWidth}, clientW=${rect.width}`);
    console.log(`Overflow? ${overflow}`);

    if (overflow) {
      let size = parseFloat(window.getComputedStyle(el).fontSize);
      let safety = 0;
      while ((el.scrollHeight > rect.height || el.scrollWidth > rect.width) && size > 7 && safety < 50) {
        size -= 0.2;
        el.style.fontSize = `${size}px`;
        safety++;
      }
      console.log(`Fixed overflow: new font=${size.toFixed(2)}px`);
    } else {
      let size = parseFloat(window.getComputedStyle(el).fontSize);
      let safety = 0;
      while (el.scrollHeight < rect.height * 0.75 && size < 12 && safety < 50) {
        size += 0.2;
        el.style.fontSize = `${size}px`;
        safety++;
      }
      console.log(`Adjusted spacing: final font=${size.toFixed(2)}px`);
    }
    console.groupEnd();
  });
}

/* -------------------------------------------------------------
   Auto-size card text (integrated)
   ------------------------------------------------------------- */
function autoSizeCardTextDebug() {
  Object.keys(cardTypeStats).forEach(k => (cardTypeStats[k] = [])); // reset stats

  // single cards
  document.querySelectorAll('.card-single').forEach(card => {
    const textEl = card.querySelector('.card-text');
    const bodyEl = card.querySelector('.card-body');
    if (!textEl || !bodyEl) return;
    const header = card.querySelector('.card-header');
    const footer = card.querySelector('.card-footer');
    const attrs = bodyEl.querySelector('.card-attrs');
    const attrInfo = bodyEl.querySelector('.card-attr-info');
    calculateOptimalFontSizePx(card, textEl, bodyEl, header, footer, attrs, attrInfo, false);
  });

  // double/triple wide cards
  document.querySelectorAll('.card-wide').forEach(card => {
    const contentEl = card.querySelector('.card-content');
    if (!contentEl) return;
    const textEl = contentEl.querySelector('.card-text');
    if (!textEl) return;
    const header = card.querySelector('.card-header-group');
    const footer = card.querySelector('.card-footer-group');
    const attrs = contentEl.querySelector('.card-attrs');
    const attrInfo = contentEl.querySelector('.card-attr-info');
    calculateOptimalFontSizePx(card, textEl, contentEl, header, footer, attrs, attrInfo, true);
  });

  debugAndFixOverflow(".card-text");
  logCardTypeStats();
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
   Throttle helper
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
  };
}

/* -------------------------------------------------------------
   Main auto-size sequence
   ------------------------------------------------------------- */
const autoSizeAll = throttle(() => {
  autoSizeCardTitle();
  autoSizeCardTextDebug();
}, 100);

document.addEventListener('DOMContentLoaded', () => {
  autoSizeAll();
  waitForLayoutStable(() => {
    console.log('Layout stabilized — final sizing pass');
    autoSizeAll();
  });
  const mo = new MutationObserver(() => debugAndFixOverflow(".card-text"));
  mo.observe(document.body, { childList: true, subtree: true });
});

window.addEventListener('resize', autoSizeAll);
