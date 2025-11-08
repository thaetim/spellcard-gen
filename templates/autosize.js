/* -------------------------------------------------------------
   Auto‑size card title (unchanged from your original version)
   ------------------------------------------------------------- */
function autoSizeCardTitle() {
    const cards = document.querySelectorAll('.card');

    cards.forEach(card => {
        const title = card.querySelector('.card-title');
        if (!title) return;

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
        while (multiline && fontSize > minSize) {
            fontSize -= 0.1;
            title.style.fontSize = fontSize + 'pt';
            void title.offsetHeight;
            multiline = isMultiline();
        }
    });
}

/* -------------------------------------------------------------
   Enhanced auto‑size for the description text
   ------------------------------------------------------------- */
function autoSizeCardText() {
    const cards = document.querySelectorAll('.card');

    cards.forEach(card => {
        const textEl   = card.querySelector('.card-text');
        const bodyEl   = card.querySelector('.card-body');
        const header   = card.querySelector('.card-header');
        const footer   = card.querySelector('.card-footer');
        const attrs    = bodyEl?.querySelector('.card-attrs');
        const attrInfo = bodyEl?.querySelector('.card-attr-info');

        if (!textEl || !bodyEl) return;

        /* ---- start values ---- */
        let fontSize = 7;                 // pt – matches your CSS default
        const minSize = 4;                // pt – never go smaller than this

        /* ---- linear line‑height function ---- */
        const lineHeightFor = size => {
            const maxSize = 7, minSizeL = 4;
            const maxLH = 1.2, minLH = 0.9;
            const t = (size - minSizeL) / (maxSize - minSizeL); // 0‑1
            return minLH + t * (maxLH - minLH);
        };

        textEl.style.fontSize   = fontSize + 'pt';
        textEl.style.lineHeight = lineHeightFor(fontSize);

        /* ---- compute how much vertical space the text may occupy ---- */
        const cardHeight   = card.offsetHeight;
        const headerH      = header ? header.offsetHeight : 0;
        const footerH      = footer ? footer.offsetHeight + 1 : 0;
        const attrsH       = attrs ? attrs.offsetHeight : 0;
        const attrInfoH    = attrInfo ? attrInfo.offsetHeight : 0;
        const bodyPad      = 4;   // top padding in pt (from your CSS)
        const textMargin   = 3;   // margin‑top in pt (from your CSS)
        const safetyMargin = 2;   // extra pixels so we don’t stop too early

        const availableHeight = cardHeight - headerH - footerH
                               - attrsH - attrInfoH
                               - bodyPad - textMargin - 5 - safetyMargin;

        /* ---- shrink until it fits ---- */
        while (textEl.scrollHeight > availableHeight && fontSize > minSize) {
            fontSize -= 0.05;                     // finer step
            textEl.style.fontSize   = fontSize + 'pt';
            textEl.style.lineHeight = lineHeightFor(fontSize);
            void textEl.offsetHeight;             // force reflow
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