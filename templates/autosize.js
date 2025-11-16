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

// Enhanced layout stabilization with multiple metrics
function waitForLayoutStable(selector, callback, maxTries = 75) {
    const container = document.querySelector(selector) || document.body;
    if (!container) {
        console.warn("No container found:", selector);
        return;
    }

    let tries = 0;
    let lastHeight = container.scrollHeight;
    let lastWidth = container.scrollWidth;

    const interval = setInterval(() => {
        const newHeight = container.scrollHeight;
        const newWidth = container.scrollWidth;
        const heightDiff = Math.abs(newHeight - lastHeight);
        const widthDiff = Math.abs(newWidth - lastWidth);

        if (heightDiff < 0.1 && widthDiff < 0.1) {
            clearInterval(interval);
            console.log("Layout fully stabilized");
            setTimeout(callback, 50); // Extra safety delay
        } else if (++tries > maxTries) {
            clearInterval(interval);
            console.warn("Layout not stable, proceeding anyway");
            setTimeout(callback, 100);
        }
        lastHeight = newHeight;
        lastWidth = newWidth;
    }, 80);
}

// Comprehensive overflow detection with Range API and line-height awareness
function isOverflowing(el) {
    if (!el) return false;
    
    // Force synchronous layout
    const rect = el.getBoundingClientRect();
    const computedStyle = window.getComputedStyle(el);
    
    // Method 1: Check height overflow with scroll comparison
    const clientHeight = Math.floor(rect.height);
    const scrollHeight = Math.floor(el.scrollHeight);
    const heightOverflow = scrollHeight > clientHeight + 1; // 1px tolerance
    
    // Method 2: Check width overflow
    const clientWidth = Math.floor(rect.width);
    const scrollWidth = Math.floor(el.scrollWidth);
    const widthOverflow = scrollWidth > clientWidth + 1;
    
    // Method 3: Range API for actual text content measurement (more accurate)
    let textOverflows = false;
    try {
        const range = document.createRange();
        range.selectNodeContents(el);
        const textRect = range.getBoundingClientRect();
        // Check if actual text content exceeds container
        textOverflows = textRect.height > clientHeight + 1 || textRect.width > clientWidth + 1;
    } catch (e) {
        // Fallback to scroll method if Range API fails
        textOverflows = false;
    }
    
    // Method 4: Special handling for multi-column layouts
    const isMultiColumn = computedStyle.columnCount !== 'auto' && 
                         parseInt(computedStyle.columnCount) > 1;
    
    if (isMultiColumn) {
        // For columns, check if content spills beyond visible area
        const columnGap = parseInt(computedStyle.columnGap) || 0;
        const columnWidth = parseInt(computedStyle.columnWidth) || (clientWidth / parseInt(computedStyle.columnCount));
        const estimatedContentWidth = (scrollWidth * parseInt(computedStyle.columnCount)) + (columnGap * (parseInt(computedStyle.columnCount) - 1));
        const columnOverflow = estimatedContentWidth > clientWidth;
        
        return heightOverflow || widthOverflow || columnOverflow || textOverflows;
    }
    
    // Method 5: Line height awareness - check if we have more lines than fit
    const lineHeight = parseFloat(computedStyle.lineHeight);
    let lineOverflow = false;
    if (lineHeight && lineHeight > 0 && !isNaN(lineHeight)) {
        const maxLines = Math.floor(clientHeight / lineHeight);
        const actualLines = Math.ceil(scrollHeight / lineHeight);
        lineOverflow = actualLines > maxLines;
    }
    
    return heightOverflow || widthOverflow || textOverflows || lineOverflow;
}

// Robust font size calculation with fallbacks
function calculateOptimalFontSize(card) {
    const cardContent = card.querySelector('.card-content');
    if (!cardContent) return null;

    // Store original state
    const originalFontSize = cardContent.style.fontSize;
    const originalDisplay = cardContent.style.display;
    
    // Ensure element is visible for accurate measurements
    cardContent.style.display = 'block';
    
    // Font size boundaries
    const absoluteMinFont = 6.5; // Absolute minimum for readability
    const absoluteMinTableFont = 4; // Absolute minimum for tables
    let minFont = 7;
    let maxFont = 11; // Increase max to allow larger text
    let bestFit = minFont;

    try {
        // Test at max font first
        cardContent.style.fontSize = maxFont + "pt";
        forceReflow(cardContent);
        
        if (!isOverflowing(cardContent)) {
            return maxFont; // Perfect fit at maximum
        }

        // Enhanced binary search with better precision
        const precision = 0.01;
        let iteration = 0;
        let lastWorkingSize = minFont;
        
        while (maxFont - minFont > precision && iteration++ < 200) {
            const mid = (minFont + maxFont) / 2;
            cardContent.style.fontSize = mid + "pt";
            forceReflow(cardContent);

            if (isOverflowing(cardContent)) {
                maxFont = mid - precision;
            } else {
                bestFit = mid;
                lastWorkingSize = mid;
                minFont = mid + precision;
            }
        }

        // Apply best fit and test
        bestFit = Math.max(bestFit, lastWorkingSize);
        cardContent.style.fontSize = bestFit + "pt";
        forceReflow(cardContent);

        // Progressive emergency reduction with multiple strategies
        let emergencyTries = 0;
        const maxEmergencyTries = 50;
        
        while (isOverflowing(cardContent) && emergencyTries < maxEmergencyTries && bestFit > absoluteMinFont) {
            // Adaptive step size based on remaining tries
            const remainingTries = maxEmergencyTries - emergencyTries;
            const step = remainingTries > 30 ? 0.2 : 
                        remainingTries > 15 ? 0.1 : 
                        0.05;
            
            bestFit = Math.max(bestFit - step, absoluteMinFont);
            cardContent.style.fontSize = bestFit + "pt";
            forceReflow(cardContent);
            emergencyTries++;
            
            // Emergency breakout if we're making no progress
            if (emergencyTries > 10 && isOverflowing(cardContent)) {
                // Try more aggressive reduction
                bestFit = Math.max(bestFit - 0.3, absoluteMinFont);
                cardContent.style.fontSize = bestFit + "pt";
                forceReflow(cardContent);
            }
        }

        // Final safety pass - ensure no overflow at any cost
        if (isOverflowing(cardContent) && bestFit > absoluteMinFont) {
            console.warn(`Final emergency reduction for card`);
            while (isOverflowing(cardContent) && bestFit > absoluteMinFont) {
                bestFit = Math.max(bestFit - 0.05, absoluteMinFont);
                cardContent.style.fontSize = bestFit + "pt";
                forceReflow(cardContent);
            }
        }

        // Apply safety margin if we found a working size
        if (!isOverflowing(cardContent)) {
            const safetyMargin = 0.10; // Reduced safety margin for tighter fit
            const safeSize = Math.max(bestFit - safetyMargin, absoluteMinFont);
            cardContent.style.fontSize = safeSize + "pt";
            forceReflow(cardContent);
            
            // Verify safety margin didn't break it
            if (!isOverflowing(cardContent)) {
                bestFit = safeSize;
            }
        }

        return Math.max(bestFit, absoluteMinFont);

    } catch (error) {
        console.error('Error calculating font size:', error);
        return 7; // Fallback size
    } finally {
        // Restore original display state
        cardContent.style.display = originalDisplay;
    }
}

// Utility function to force browser reflow
function forceReflow(element) {
    void element.offsetHeight;
    void element.offsetWidth;
    void element.getBoundingClientRect();
}

function applyFontSizeToCard(card, fontSize) {
    const absoluteMinFont = 6.5;
    const absoluteMinTableFont = 4;
    
    const cardContent = card.querySelector('.card-content');
    if (cardContent) {
        cardContent.style.fontSize = fontSize.toFixed(2) + "pt";
        forceReflow(cardContent);
        
        // Set table font size to be equal to or smaller than main text
        const tables = cardContent.querySelectorAll('.card-text table');
        tables.forEach(table => {
            table.style.fontSize = fontSize.toFixed(2) + "pt";
        });
        
        // Final verification - if still overflowing, shrink tables first
        if (isOverflowing(cardContent)) {
            let tableFontSize = fontSize;
            // First try shrinking tables independently
            while (isOverflowing(cardContent) && tableFontSize > absoluteMinTableFont && tables.length > 0) {
                tableFontSize -= 0.1;
                tables.forEach(table => {
                    table.style.fontSize = tableFontSize.toFixed(2) + "pt";
                });
                forceReflow(cardContent);
            }
            
            // If still overflowing after shrinking tables, shrink everything
            if (isOverflowing(cardContent)) {
                console.warn(`Card STILL overflowing at ${fontSize.toFixed(2)}pt - applying emergency fix`);
                let emergencySize = fontSize;
                while (isOverflowing(cardContent) && emergencySize > absoluteMinFont) {
                    emergencySize -= 0.1;
                    cardContent.style.fontSize = emergencySize.toFixed(2) + "pt";
                    tables.forEach(table => {
                        // Tables should never be larger than main text
                        const currentTableSize = parseFloat(table.style.fontSize);
                        table.style.fontSize = Math.min(currentTableSize, emergencySize).toFixed(2) + "pt";
                    });
                    forceReflow(cardContent);
                }
                return emergencySize;
            }
        }
    }
    return fontSize;
}

function autoSizeAllCards() {
    const cards = document.querySelectorAll('.card-single, .card-double, .card-triple');
    if (!cards.length) {
        console.warn("No cards found for autosizing");
        return;
    }

    let singles = 0, doubles = 0, triples = 0;
    let overflowCount = 0;

    console.log('Starting font sizing for', cards.length, 'cards');

    // Reset all cards to default state
    cards.forEach(card => {
        const cardContent = card.querySelector('.card-content');
        if (cardContent) {
            cardContent.style.fontSize = '';
            cardContent.style.display = 'block';
        }
    });

    // Major layout force
    forceReflow(document.body);
    
    // Process cards in batches to avoid layout thrashing
    const processCardBatch = (cardBatch, index) => {
        // console.log(`Processing batch ${index + 1} of ${cardBatch.length} cards`);
        
        cardBatch.forEach((card, cardIndex) => {
            // Small delay between cards to allow layout
            setTimeout(() => {
                if (card.classList.contains('card-single')) {
                    singles++;
                } else if (card.classList.contains('card-double')) {
                    doubles++;
                } else if (card.classList.contains('card-triple')) {
                    triples++;
                }

                const optimalSize = calculateOptimalFontSize(card);
                if (optimalSize !== null) {
                    const finalSize = applyFontSizeToCard(card, optimalSize);
                    
                    const cardContent = card.querySelector('.card-content');
                    const cardType = card.classList.contains('card-single') ? 'single' : 
                                    card.classList.contains('card-double') ? 'double' : 'triple';
                    
                    const overflowing = isOverflowing(cardContent);
                    if (overflowing) {
                        overflowCount++;
                        console.error(`❌ ${cardType} card STILL OVERFLOWING at ${finalSize.toFixed(2)}pt`);
                    } else {
                        // console.log(`✅ ${cardType} card sized to ${finalSize.toFixed(2)}pt`);
                    }
                }
            }, cardIndex * 20); // Stagger card processing
        });
    };

    // Process cards in smaller batches
    const batchSize = 5;
    for (let i = 0; i < cards.length; i += batchSize) {
        const batch = Array.from(cards).slice(i, i + batchSize);
        processCardBatch(batch, i / batchSize);
    }

    // Final report
    setTimeout(() => {
        console.log(`Font sizing complete — singles=${singles}, doubles=${doubles}, triples=${triples}`);
        console.log(`${overflowCount} cards with overflow issues`);
        
        if (overflowCount > 0) {
            console.error(`❌ ${overflowCount} cards still have overflow issues - check CSS constraints`);
        } else {
            console.log('✅ All cards properly sized!');
        }
    }, cards.length * 25 + 1000);
}

const autoSizeAll = throttle(() => {
    console.clear();
    autoSizeAllCards();
}, 500);

// Enhanced event listeners
window.addEventListener('load', () => {
    setTimeout(() => waitForLayoutStable('body', autoSizeAll), 500);
});

// window.addEventListener('resize', throttle(() => {
//     console.log('Window resized - recalculating fonts');
//     autoSizeAll();
// }, 600));

// Export for manual triggering if needed
window.triggerFontResize = autoSizeAll;

})();