"""dark_theme_qss.py — Dark theme QSS stylesheet constant."""
# This constant is imported by MainWindow and applied via setStyleSheet().
DARK_THEME_QSS = """
    QMainWindow, QWidget#CentralWidget {
        background-color: #1a1a2e;
        color: #e0e0e6;
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    }
    QFrame#HeaderBar {
        background-color: #16213e;
        border-bottom: 1px solid #0f3460;
        border-radius: 6px;
        padding: 6px 12px;
    }
    QLabel {
        color: #d1d5db;
        font-size: 13px;
    }
    QLabel#AppTitle {
        font-weight: 700;
        font-size: 14px;
        color: #ffffff;
        letter-spacing: 0.5px;
    }
    QLabel#BadgeLive {
        background-color: #0f3460;
        color: #4ade80;
        font-size: 11px;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 4px;
        border: 1px solid #16537e;
    }
    QLabel#BadgeMode {
        background-color: #0f3460;
        color: #60a5fa;
        font-size: 11px;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 4px;
    }
    /* Minimal Tab Styling */
    QTabWidget::pane {
        border: 1px solid #0f3460;
        background-color: #16213e;
        border-radius: 6px;
        margin-top: -1px;
    }
    QTabBar::tab {
        background-color: transparent;
        color: #9ca3af;
        padding: 10px 18px;
        margin-right: 2px;
        font-weight: 500;
        border-bottom: 2px solid transparent;
    }
    QTabBar::tab:selected {
        color: #ffffff;
        font-weight: 600;
        border-bottom: 2px solid #e94560;
        background-color: #16213e;
    }
    QTabBar::tab:hover:!selected {
        color: #e2e8f0;
        background-color: rgba(15, 52, 96, 0.3);
    }
    /* Action Buttons */
    QPushButton {
        background-color: #0f3460;
        color: #ffffff;
        border: 1px solid #1a4f8b;
        border-radius: 4px;
        padding: 6px 14px;
        font-weight: 500;
        font-size: 12px;
    }
    QPushButton:hover {
        background-color: #174276;
    }
    QPushButton#StopBtn {
        background-color: #e94560;
        border: 1px solid #ff5a77;
    }
    QPushButton#StopBtn:hover {
        background-color: #d13b53;
    }
    /* KPI Cards */
    QFrame#KPICard {
        background-color: #1a1a2e;
        border: 1px solid #0f3460;
        border-radius: 6px;
        padding: 12px;
    }
    QStatusBar {
        background-color: #16213e;
        color: #9ca3af;
        border-top: 1px solid #0f3460;
        font-size: 11px;
    }
"""
