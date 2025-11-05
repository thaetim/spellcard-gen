function autoSizeCardTitle() {
    const cards = document.querySelectorAll('.card');
    
    cards.forEach((card) => {
        const titleElement = card.querySelector('.card-title');
        if (!titleElement) return;
        
        // Reset to default
        let fontSize = 17;
        const minFontSize = 15;
        titleElement.style.fontSize = fontSize + 'pt';
        titleElement.style.lineHeight = '1.1'; // Tight line height for titles
        titleElement.style.overflow = 'hidden';
        
        // Force initial layout calculation
        void titleElement.offsetHeight;
        
        // Function to check if title is multiline
        const isMultiline = () => {
            // Store current styles that might affect height
            const originalWhiteSpace = titleElement.style.whiteSpace;
            titleElement.style.whiteSpace = 'nowrap';
            void titleElement.offsetHeight; // Force reflow
            
            const singleLineHeight = titleElement.offsetHeight;
            
            // Restore original white-space
            titleElement.style.whiteSpace = originalWhiteSpace;
            void titleElement.offsetHeight; // Force reflow again
            
            const currentHeight = titleElement.offsetHeight;
            
            // If current height is significantly greater than single line height, it's multiline
            // Using 1.5 multiplier to account for line height variations
            return currentHeight > singleLineHeight * 1.5;
        };
        
        // Initial check
        let isCurrentlyMultiline = isMultiline();
        
        // Continue shrinking while title is multiline and we're above minimum size
        while (isCurrentlyMultiline && fontSize > minFontSize) {
            // Reduce font size
            fontSize -= 0.1;
            titleElement.style.fontSize = fontSize + 'pt';
            
            // Force reflow to ensure new size is rendered
            void titleElement.offsetHeight;
            
            // Check if it's still multiline with the new size
            isCurrentlyMultiline = isMultiline();
            
            console.log(`Font size: ${fontSize}pt, Multiline: ${isCurrentlyMultiline}`);
        }
        
        // Optional: If we hit minimum size and it's still multiline, 
        // we could apply ellipsis or other fallback
        if (isCurrentlyMultiline && fontSize === minFontSize) {
            console.log('Title still multiline at minimum font size');
            // titleElement.style.textOverflow = 'ellipsis';
        }
    });
}

function autoSizeCardText() {
    const cards = document.querySelectorAll('.card');

    cards.forEach((card) => {
        const textElement = card.querySelector('.card-text');
        const cardBody = card.querySelector('.card-body');
        const cardHeader = card.querySelector('.card-header');
        const cardFooter = card.querySelector('.card-footer');
        const attrs = cardBody?.querySelector('.card-attrs');
        const attrInfo = cardBody?.querySelector('.card-attr-info');

        if (!textElement || !cardBody) return;

        // Reset to default
        let fontSize = 8;
        const lineHeightRatio = 1.2;
        textElement.style.fontSize = fontSize + 'pt';
        textElement.style.lineHeight = lineHeightRatio;

        // Force layout recalculation
        void textElement.offsetHeight;

        // Calculate fixed heights
        const cardHeight = card.offsetHeight;
        const headerHeight = cardHeader ? cardHeader.offsetHeight : 0;
        const footerHeight = cardFooter ? cardFooter.offsetHeight + 5 : 0;
        const attrsHeight = attrs ? attrs.offsetHeight : 0;
        const attrInfoHeight = attrInfo ? attrInfo.offsetHeight : 0;

        // Account for card-body padding (4pt top, 5pt left/right, 0 bottom)
        const bodyPadding = 4;
        // Account for card-text margin-top
        const textMargin = 3;

        const availableHeight = cardHeight - headerHeight - footerHeight - attrsHeight - attrInfoHeight - bodyPadding - textMargin - 5;

        // Shrink font until it fits
        while (textElement.scrollHeight > availableHeight && fontSize > 4) {
            fontSize -= 0.1;
            textElement.style.fontSize = fontSize + 'pt';
            textElement.style.lineHeight = fontSize < 6 ? 1.0 : 1.2;
            void textElement.offsetHeight; // Force reflow
        }
    });
}

function waitForLayoutStable(callback, interval = 200, stableCount = 3) {
    let lastHeightSum = 0;
    let stableTicks = 0;

    const timer = setInterval(() => {
        const totalHeight = [...document.querySelectorAll('.card-text')]
            .map(e => e.scrollHeight)
            .reduce((a, b) => a + b, 0);

        if (totalHeight === lastHeightSum) {
            stableTicks++;
        } else {
            stableTicks = 0;
            lastHeightSum = totalHeight;
        }

        if (stableTicks >= stableCount) {
            clearInterval(timer);
            callback();
        }
    }, interval);
}

function autoSizeAll() {
    autoSizeCardTitle();
    autoSizeCardText();
}

document.addEventListener('DOMContentLoaded', () => {
    // First run soon after DOM ready
    autoSizeAll();

    // Wait until layout stops changing, then rerun for final sizing
    waitForLayoutStable(() => {
        console.log("Layout stabilized — final autoSizeAll()");
        autoSizeAll();
    });
});

// Re-adjust if browser window resizes
window.addEventListener('resize', autoSizeAll);
