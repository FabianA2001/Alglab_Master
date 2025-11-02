// Shift Plan Table Configuration
window.SHIFT_PLAN_CONFIG = {
    // Spaltenbreiten
    columns: {
        shiftTypeMinWidth: '80px',
        dayMinWidth: '100px'
    },

    // Farben
    colors: {
        // Header Farben
        headerBackground: '#f5f5f5',
        shiftTypeHeaderBackground: '#4CAF50',
        shiftTypeHeaderText: '#ffffff',
        
        // Tabellen Farben
        tableBorder: '#e0e0e0',
        tableHoverBackground: '#f9f9f9',
        
        // Mitarbeiter Badge Farben
        employeeBadgeBackground: '#e3f2fd',
        employeeBadgeText: '#1976d2',
        
        // Highlight Farben (für Suche)
        highlightBackground: '#fff9c4',
        highlightBadgeBackground: '#ffeb3b',
        highlightBadgeText: '#000000',
        
        // Leere Zelle
        emptyCellText: '#999999',
        
        // Info Text
        infoText: '#666666'
    },

    // Padding und Abstände
    spacing: {
        cellPadding: '12px',
        badgeGap: '6px',
        badgePadding: '4px 8px',
        containerPadding: '20px',
        filterMarginBottom: '16px',
        infoMarginTop: '12px'
    },

    // Schriftgrößen
    fonts: {
        badgeFontSize: '0.85em',
        infoFontSize: '0.9em',
        filterFontSize: '0.9em'
    },

    // Border Radius
    borderRadius: {
        container: '8px',
        badge: '4px',
        filterInput: '4px'
    },

    // Schatten
    shadows: {
        container: '0 2px 4px rgba(0, 0, 0, 0.1)'
    },

    // Text und Labels
    text: {
        shiftTypeHeader: 'Schichttyp',
        dayHeaderPrefix: 'Tag',
        searchPlaceholder: 'Nach Mitarbeiter suchen...',
        emptyCell: '-',
        infoTemplate: (shiftTypes, days, assignments) => 
            `Gesamt: ${shiftTypes} Schichttypen, ${days} Tage, ${assignments} Zuweisungen`
    },

    // Komponenten Höhe und Breite
    dimensions: {
        componentHeight: 600,
        tableMinWidth: '600px',
        filterInputWidth: '300px'
    },

    // Verhalten
    behavior: {
        enableSearch: true,
        enableHover: true,
        scrolling: true,
        caseSensitiveSearch: false
    }
};

// Debug: Bestätige dass Config geladen wurde
console.log('SHIFT_PLAN_CONFIG loaded:', window.SHIFT_PLAN_CONFIG);
