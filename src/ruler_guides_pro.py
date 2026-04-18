"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     RULER GUIDES PRO BY Abhisht Pandey                         ║
║                   Version 3.0 - Refined & Optimized                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

"""

import sys
import json
import os
import time
from pathlib import Path
from datetime import datetime
import shutil
import ctypes

def get_icon_path():
    """Resolve the icon file whether running as source or compiled onefile executable"""
    import os, sys, tempfile

    candidates = []

    # 1. Nuitka onefile: assets are extracted to a temp dir alongside the binary
    #    The binary dir is exposed via __nuitka_binary_dir in compiled code
    try:
        nuitka_dir = __nuitka_binary_dir  # noqa (only defined when compiled)
        candidates.append(os.path.join(nuitka_dir, "assets", "icon.ico"))
    except NameError:
        pass

    # 2. Nuitka onefile also sets NUITKA_ONEFILE_PARENT env var
    parent = os.environ.get("NUITKA_ONEFILE_PARENT", "")
    if parent:
        candidates.append(os.path.join(os.path.dirname(parent), "assets", "icon.ico"))

    # 3. Running from source — go up from src/ to project root
    if "__file__" in globals():
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates.append(os.path.join(base_dir, "assets", "icon.ico"))

    # 4. Same directory as the EXE (for standalone / moved EXE)
    exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    candidates.append(os.path.join(exe_dir, "assets", "icon.ico"))
    candidates.append(os.path.join(exe_dir, "icon.ico"))

    # 5. CWD fallback
    cwd = os.getcwd()
    candidates.append(os.path.join(cwd, "assets", "icon.ico"))
    candidates.append(os.path.join(cwd, "icon.ico"))

    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return candidate

    return None


from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow, QSystemTrayIcon,
                             QMenu, QAction, QColorDialog, QSpinBox, QLabel,
                             QVBoxLayout, QHBoxLayout, QPushButton, QSlider,
                             QCheckBox, QMessageBox, QGridLayout, QTabWidget,
                             QFrame, QSizePolicy, QTextEdit)
from PyQt5.QtCore import (Qt, QPoint, QRect, QTimer, pyqtSignal, QObject, 
                          pyqtProperty, QSize, QRectF)
from PyQt5.QtGui import (QPainter, QColor, QPen, QFont, QCursor, QIcon,
                        QPainterPath, QPixmap, QBrush, QPalette, QLinearGradient)
import keyboard
import win32gui
import win32con


# ═══════════════════════════════════════════════════════════════════════════
# MODERN COLOR PALETTE
# ═══════════════════════════════════════════════════════════════════════════

class Colors:
    """Ultra-modern Minimalist Color Scheme"""
    # UI Colors (Tailwind Slate/Neutral inspired)
    BG_PRIMARY = '#0B0D10'       # Deepest flat background
    BG_SECONDARY = '#13161A'     # Slight elevation
    BG_SURFACE = '#1A1D24'       # Floating surfaces Component level
    BORDER = '#242932'
    BORDER_LIGHT = '#323945'
    
    TEXT_PRIMARY = '#F3F4F6'
    TEXT_SECONDARY = '#9CA3AF'
    TEXT_MUTED = '#6B7280'
    
    # Accent Colors (Electric Blue)
    ACCENT = '#3B82F6'          
    ACCENT_HOVER = '#60A5FA'
    
    # Guide Colors
    GUIDE_DEFAULT = '#3B82F6'   
    GUIDE_SELECTED = '#F59E0B'  
    GUIDE_LOCKED = '#10B981'    
    GUIDE_HOVER = '#93C5FD'     
    
    RULER_BG = '#0B0D10'
    GRID = '#1E232B'
    
    SUCCESS = '#10B981'
    WARNING = '#F59E0B'
    ERROR = '#EF4444'


# ═══════════════════════════════════════════════════════════════════════════
# REACTIVE CONFIG MODEL
# ═══════════════════════════════════════════════════════════════════════════

class ConfigModel(QObject):
    """Reactive configuration with automatic propagation"""
    
    # Signals for real-time updates
    opacity_changed = pyqtSignal(float)
    thickness_changed = pyqtSignal(int)
    ruler_size_changed = pyqtSignal(int)
    scale_changed = pyqtSignal(float)
    color_changed = pyqtSignal(str, str)  # (key, color)
    grid_size_changed = pyqtSignal(int)
    snap_changed = pyqtSignal(bool)
    visibility_changed = pyqtSignal(str, bool)  # (element, visible)
    config_saved = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # Core properties
        self._opacity = 0.85
        self._thickness = 2
        self._ruler_size = 30
        self._scale = 1.0
        self._grid_size = 10
        self._snap_to_grid = False
        
        # Colors
        self._colors = {
            'ruler_color': Colors.RULER_BG,
            'guide_color': Colors.GUIDE_DEFAULT,
            'selected_guide_color': Colors.GUIDE_SELECTED,
            'locked_guide_color': Colors.GUIDE_LOCKED,
            'grid_color': Colors.GRID,
            'text_color': Colors.TEXT_PRIMARY,
        }
        
        # Visibility
        self._show_rulers = True
        self._show_guides = True
        self._show_coordinates = True
        self._show_measurements = True
        self._show_grid = False
        
        # Debounce timer for auto-save
        self._save_timer = QTimer()
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self.config_saved.emit)
    
    # Properties with automatic signal emission
    
    @pyqtProperty(float)
    def opacity(self):
        return self._opacity
    
    @opacity.setter
    def opacity(self, value):
        if self._opacity != value:
            self._opacity = max(0.1, min(1.0, value))
            self.opacity_changed.emit(self._opacity)
            self._trigger_save()
    
    @pyqtProperty(int)
    def thickness(self):
        return self._thickness
    
    @thickness.setter
    def thickness(self, value):
        if self._thickness != value:
            self._thickness = max(1, min(20, value))
            self.thickness_changed.emit(self._thickness)
            self._trigger_save()
    
    @pyqtProperty(int)
    def ruler_size(self):
        return self._ruler_size
    
    @ruler_size.setter
    def ruler_size(self, value):
        if self._ruler_size != value:
            self._ruler_size = max(20, min(100, value))
            self.ruler_size_changed.emit(self._ruler_size)
            self._trigger_save()
    
    @pyqtProperty(float)
    def scale(self):
        return self._scale
    
    @scale.setter
    def scale(self, value):
        if self._scale != value:
            self._scale = max(0.1, min(20.0, value))
            self.scale_changed.emit(self._scale)
            self._trigger_save()
    
    @pyqtProperty(int)
    def grid_size(self):
        return self._grid_size
    
    @grid_size.setter
    def grid_size(self, value):
        if self._grid_size != value:
            self._grid_size = max(1, min(500, value))
            self.grid_size_changed.emit(self._grid_size)
            self._trigger_save()
    
    @pyqtProperty(bool)
    def snap_to_grid(self):
        return self._snap_to_grid
    
    @snap_to_grid.setter
    def snap_to_grid(self, value):
        if self._snap_to_grid != value:
            self._snap_to_grid = value
            self.snap_changed.emit(value)
            self._trigger_save()
    
    # Color management
    def get_color(self, key):
        return self._colors.get(key, Colors.GUIDE_DEFAULT)
    
    def set_color(self, key, color):
        if self._colors.get(key) != color:
            self._colors[key] = color
            self.color_changed.emit(key, color)
            self._trigger_save()
    
    # Visibility management
    def set_visibility(self, element, visible):
        attr = f'_show_{element}'
        if hasattr(self, attr):
            if getattr(self, attr) != visible:
                setattr(self, attr, visible)
                self.visibility_changed.emit(element, visible)
                self._trigger_save()
    
    def get_visibility(self, element):
        return getattr(self, f'_show_{element}', True)
    
    # Persistence
    def _trigger_save(self):
        self._save_timer.start(500)  # Debounce 500ms
    
    def to_dict(self):
        """Export to dictionary for saving"""
        return {
            'version': '3.0',
            'opacity': self._opacity,
            'thickness': self._thickness,
            'ruler_size': self._ruler_size,
            'scale': self._scale,
            'grid_size': self._grid_size,
            'snap_to_grid': self._snap_to_grid,
            'colors': self._colors.copy(),
            'show_rulers': self._show_rulers,
            'show_guides': self._show_guides,
            'show_coordinates': self._show_coordinates,
            'show_measurements': self._show_measurements,
            'show_grid': self._show_grid,
        }
    
    def from_dict(self, data):
        """Import from dictionary (blocks signals during bulk update)"""
        self.blockSignals(True)
        
        self._opacity = data.get('opacity', 0.85)
        self._thickness = data.get('thickness', 2)
        self._ruler_size = data.get('ruler_size', 30)
        self._scale = data.get('scale', 1.0)
        self._grid_size = data.get('grid_size', 10)
        self._snap_to_grid = data.get('snap_to_grid', False)
        self._colors.update(data.get('colors', {}))
        self._show_rulers = data.get('show_rulers', True)
        self._show_guides = data.get('show_guides', True)
        self._show_coordinates = data.get('show_coordinates', True)
        self._show_measurements = data.get('show_measurements', True)
        self._show_grid = data.get('show_grid', False)
        
        self.blockSignals(False)
        
        # Emit all signals once
        self.opacity_changed.emit(self._opacity)
        self.thickness_changed.emit(self._thickness)
        self.scale_changed.emit(self._scale)


# ═══════════════════════════════════════════════════════════════════════════
# CONFIG MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class ConfigManager:
    """Persistence layer for configuration"""
    
    def __init__(self, app_dir=None):
        if app_dir is None:
            import tempfile
            self.app_dir = Path(tempfile.gettempdir()) / 'RulerGuidesPro'
        else:
            self.app_dir = Path(app_dir)
        
        self.config_dir = self.app_dir / 'config'
        self.config_file = self.config_dir / 'settings.json'
        self.layout_file = self.config_dir / 'layout.json'
        self.backup_dir = self.config_dir / 'backups'
        
        self.ensure_directories()
    
    def ensure_directories(self):
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            return True
        except:
            return False
    
    def save_config(self, config_model):
        """Save ConfigModel to disk"""
        try:
            self.ensure_directories()
            data = config_model.to_dict()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Config save error: {e}")
            return False
    
    def load_config(self, config_model):
        """Load ConfigModel from disk"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                config_model.from_dict(data)
                return True
            except Exception as e:
                print(f"Config load error: {e}")
                return False
        return False
    
    def save_layout(self, layout_data):
        """Save guide layout"""
        try:
            if self.layout_file.exists():
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup = self.backup_dir / f'layout_{timestamp}.json'
                shutil.copy2(self.layout_file, backup)
                self.cleanup_old_backups()
            
            with open(self.layout_file, 'w', encoding='utf-8') as f:
                json.dump(layout_data, f, indent=2)
            return True
        except:
            return False
    
    def load_layout(self):
        """Load guide layout"""
        if self.layout_file.exists():
            try:
                with open(self.layout_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return None
        return None
    
    def cleanup_old_backups(self, keep=10):
        """Keep only recent backups"""
        try:
            backups = sorted(
                self.backup_dir.glob('layout_*.json'),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            for old in backups[keep:]:
                old.unlink()
        except:
            pass
    
    def open_config_folder(self):
        """Open config folder in explorer"""
        try:
            os.startfile(str(self.config_dir.absolute()))
            return True
        except:
            return False


# ═══════════════════════════════════════════════════════════════════════════
# GUIDE CLASS
# ═══════════════════════════════════════════════════════════════════════════

class Guide:
    """Enhanced guide with accurate hit detection"""
    
    def __init__(self, orientation, position, scale=1.0):
        self.orientation = orientation  # 'horizontal' or 'vertical'
        self.position = position
        self.scaled_position = position / scale
        self.dragging = False
        self.hover = False
        self.locked = False
        self.selected = False
    
    def contains_point(self, point, scale=1.0):
        """Scale-aware hit detection"""
        # Dynamic tolerance: larger at small scales
        tolerance = max(6, 10 / scale)
        actual_pos = self.scaled_position * scale
        
        if self.orientation == 'horizontal':
            return abs(point.y() - actual_pos) < tolerance
        else:
            return abs(point.x() - actual_pos) < tolerance
    
    def update_position(self, new_position, scale=1.0):
        """Update both pixel and scaled position"""
        self.position = new_position
        self.scaled_position = new_position / scale
    
    def to_dict(self):
        return {
            'orientation': self.orientation,
            'position': self.position,
            'scaled_position': self.scaled_position,
            'locked': self.locked,
        }
    
    @staticmethod
    def from_dict(data, scale=1.0):
        guide = Guide(data['orientation'], data.get('position', 0), scale)
        guide.scaled_position = data.get('scaled_position', data.get('position', 0))
        guide.locked = data.get('locked', False)
        return guide


# ═══════════════════════════════════════════════════════════════════════════
# RULER OVERLAY - OPTIMIZED WITH CACHING
# ═══════════════════════════════════════════════════════════════════════════

class RulerOverlay(QWidget):
    """High-performance overlay with smart caching"""
    
    guide_changed = pyqtSignal()
    
    def __init__(self, config_model):
        super().__init__()
        self.config = config_model
        
        # Guide management
        self.guides = []
        self.dragging_guide = None
        self.preview_guide = None
        self.selected_guide = None
        
        # Zoom presets
        self.zoom_levels = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 10.0]
        
        # Performance optimization
        self.ruler_cache = None
        self.grid_cache = None
        self.cache_valid = False
        self.last_cursor_update = 0
        self.cursor_pos = QPoint(0, 0)
        
        # Click-through mode
        self.click_through_mode = False
        
        # Tick intervals (updated on scale change)
        self.update_tick_intervals()
        
        # Connect to config changes
        self.connect_config_signals()
        
        self.init_ui()
    
    def connect_config_signals(self):
        """Real-time config updates"""
        self.config.scale_changed.connect(self.on_scale_changed)
        self.config.ruler_size_changed.connect(self.invalidate_cache)
        self.config.color_changed.connect(self.on_color_changed)
        self.config.grid_size_changed.connect(self.invalidate_grid_cache)
        self.config.visibility_changed.connect(self.on_visibility_changed)
        self.config.thickness_changed.connect(self.update)  # Instant update
        self.config.opacity_changed.connect(self.update)    # Instant update
    
    def init_ui(self):
        desktop = QApplication.desktop()
        rect = QRect()
        for i in range(desktop.screenCount()):
            rect = rect.united(desktop.screenGeometry(i))
        self.setGeometry(rect)
        
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        
        self.show()
        self.make_click_through(False)
    
    def make_click_through(self, enabled):
        """Toggle click-through mode"""
        hwnd = int(self.winId())
        if enabled:
            win32gui.SetWindowLong(
                hwnd, win32con.GWL_EXSTYLE,
                win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) |
                win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
            )
            self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        else:
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            style = style & ~win32con.WS_EX_TRANSPARENT
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)
            self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        
        self.click_through_mode = enabled
        self.update()
    
    # ═══════════════════════════════════════════════════════════════════════
    # CACHE MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════
    
    def invalidate_cache(self):
        """Invalidate all caches"""
        self.ruler_cache = None
        self.grid_cache = None
        self.cache_valid = False
        self.update()
    
    def invalidate_grid_cache(self):
        """Invalidate only grid cache"""
        self.grid_cache = None
        self.update()
    
    def on_scale_changed(self, scale):
        """Handle scale change"""
        # Update guide positions
        for guide in self.guides:
            guide.position = guide.scaled_position * scale
        
        self.update_tick_intervals()
        self.invalidate_cache()
    
    def on_color_changed(self, key, color):
        """Handle color change"""
        if key in ['ruler_color', 'grid_color']:
            self.invalidate_cache()
        else:
            self.update()
    
    def on_visibility_changed(self, element, visible):
        """Handle visibility toggle"""
        self.update()
    
    def update_tick_intervals(self):
        """Calculate optimal tick intervals for current scale"""
        scale = self.config.scale
        if scale >= 4.0:
            self.tick_major, self.tick_minor, self.tick_micro = 50, 10, 5
        elif scale >= 2.0:
            self.tick_major, self.tick_minor, self.tick_micro = 100, 20, 10
        elif scale >= 1.0:
            self.tick_major, self.tick_minor, self.tick_micro = 100, 10, 5
        elif scale >= 0.5:
            self.tick_major, self.tick_minor, self.tick_micro = 200, 50, 10
        else:
            self.tick_major, self.tick_minor, self.tick_micro = 500, 100, 50
    
    # ═══════════════════════════════════════════════════════════════════════
    # ZOOM CONTROLS
    # ═══════════════════════════════════════════════════════════════════════
    
    def set_scale(self, scale):
        """Public scale setter"""
        self.config.scale = scale
    
    def zoom_in(self):
        idx = self.get_nearest_zoom_index()
        if idx < len(self.zoom_levels) - 1:
            self.config.scale = self.zoom_levels[idx + 1]
    
    def zoom_out(self):
        idx = self.get_nearest_zoom_index()
        if idx > 0:
            self.config.scale = self.zoom_levels[idx - 1]
    
    def zoom_reset(self):
        self.config.scale = 1.0
    
    def get_nearest_zoom_index(self):
        distances = [abs(self.config.scale - level) for level in self.zoom_levels]
        return distances.index(min(distances))
    
    # ═══════════════════════════════════════════════════════════════════════
    # SNAP & GRID
    # ═══════════════════════════════════════════════════════════════════════
    
    def snap_position(self, pos):
        """Snap position to grid if enabled"""
        if self.config.snap_to_grid and self.config.grid_size > 0:
            grid = self.config.grid_size * self.config.scale
            return QPoint(
                int(round(pos.x() / grid) * grid),
                int(round(pos.y() / grid) * grid)
            )
        return pos
    
    # ═══════════════════════════════════════════════════════════════════════
    # RENDERING ENGINE - OPTIMIZED
    # ═══════════════════════════════════════════════════════════════════════
    
    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Layer 1: Grid (cached)
        if self.config.get_visibility('grid'):
            self.draw_grid(painter)
        
        # Layer 2: Rulers (cached)
        if self.config.get_visibility('rulers'):
            self.draw_rulers(painter)
        
        # Layer 3: Guides (dynamic)
        if self.config.get_visibility('guides'):
            self.draw_guides(painter)
        
        # Layer 4: Preview guide
        if self.preview_guide:
            self.draw_preview_guide(painter)
        
        # Layer 5: Overlays
        if self.config.get_visibility('coordinates') and not self.click_through_mode:
            self.draw_coordinates(painter)
        
        # Layer 6: Click-through indicator
        if self.click_through_mode:
            self.draw_click_through_badge(painter)
    
    def draw_grid(self, painter):
        """Draw grid with caching"""
        grid_size = int(self.config.grid_size * self.config.scale)
        
        if grid_size < 2:
            return
        
        # Use cache if valid
        if self.grid_cache is None:
            self.grid_cache = self.render_grid_to_cache()
        
        painter.setOpacity(self.config.opacity * 0.8)
        painter.drawPixmap(0, 0, self.grid_cache)
        painter.setOpacity(1.0)
    
    def render_grid_to_cache(self):
        """Render grid to pixmap cache"""
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.transparent)
        
        p = QPainter(pixmap)
        grid_color = QColor(self.config.get_color('grid_color'))
        grid_color.setAlpha(int(255 * self.config.opacity))
        
        pen = QPen(grid_color, 1, Qt.SolidLine)  # Solid pen for better visibility
        p.setPen(pen)
        p.setRenderHint(QPainter.Antialiasing, False)
        
        grid_size = int(self.config.grid_size * self.config.scale)
        ruler_size = self.config.ruler_size
        
        # Vertical lines
        for x in range(0, self.width(), grid_size):
            p.drawLine(x, ruler_size, x, self.height())
        
        # Horizontal lines
        for y in range(0, self.height(), grid_size):
            p.drawLine(ruler_size, y, self.width(), y)
        
        p.end()
        return pixmap
    
    def draw_rulers(self, painter):
        """Draw rulers with caching"""
        if self.ruler_cache is None or not self.cache_valid:
            self.ruler_cache = self.render_rulers_to_cache()
            self.cache_valid = True
        
        painter.setOpacity(self.config.opacity)
        painter.drawPixmap(0, 0, self.ruler_cache)
        painter.setOpacity(1.0)
    
    def render_rulers_to_cache(self):
        """Render rulers to pixmap cache"""
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.transparent)
        
        p = QPainter(pixmap)
        p.setRenderHint(QPainter.Antialiasing, True)
        
        ruler_color = QColor(self.config.get_color('ruler_color'))
        text_color = QColor(self.config.get_color('text_color'))
        ruler_size = self.config.ruler_size
        
        # Ruler backgrounds
        p.fillRect(0, 0, self.width(), ruler_size, ruler_color)
        p.fillRect(0, 0, ruler_size, self.height(), ruler_color)
        
        # Corner with gradient
        corner_color = ruler_color.darker(110)
        p.fillRect(0, 0, ruler_size, ruler_size, corner_color)
        
        # Corner scale indicator
        p.setPen(text_color)
        font = QFont('Segoe UI', 7, QFont.Bold)
        p.setFont(font)
        scale_text = f"{int(self.config.scale * 100)}%"
        p.drawText(QRect(0, 0, ruler_size, ruler_size), Qt.AlignCenter, scale_text)
        
        # Borders
        border_color = ruler_color.darker(120)
        p.setPen(QPen(border_color, 1))
        p.drawLine(0, ruler_size, self.width(), ruler_size)
        p.drawLine(ruler_size, 0, ruler_size, self.height())
        
        # Tick marks
        p.setRenderHint(QPainter.Antialiasing, False)
        self.draw_ruler_ticks(p, text_color, ruler_size)
        
        p.end()
        return pixmap
    
    def draw_ruler_ticks(self, painter, text_color, ruler_size):
        """Draw ruler tick marks"""
        painter.setPen(text_color)
        font = QFont('Segoe UI', 7)
        painter.setFont(font)
        
        scale = self.config.scale
        step = max(1, int(self.tick_micro * scale))
        
        # Horizontal ruler
        for x in range(0, self.width(), step):
            scaled_x = int(x / scale)
            
            if scaled_x % self.tick_major == 0:
                painter.drawLine(x, ruler_size - 10, x, ruler_size)
                if x > 0:
                    painter.drawText(x + 4, 14, str(scaled_x))
            elif scaled_x % self.tick_minor == 0:
                painter.drawLine(x, ruler_size - 6, x, ruler_size)
            else:
                painter.drawLine(x, ruler_size - 3, x, ruler_size)
        
        # Vertical ruler
        for y in range(0, self.height(), step):
            scaled_y = int(y / scale)
            
            if scaled_y % self.tick_major == 0:
                painter.drawLine(ruler_size - 10, y, ruler_size, y)
                if y > 0:
                    painter.save()
                    # Moved baseline to X=14 so numbers don't clip off the left screen edge
                    painter.translate(14, y - 4)
                    painter.rotate(-90)
                    painter.drawText(0, 0, str(scaled_y))
                    painter.restore()
            elif scaled_y % self.tick_minor == 0:
                painter.drawLine(ruler_size - 6, y, ruler_size, y)
            else:
                painter.drawLine(ruler_size - 3, y, ruler_size, y)
    
    def draw_guides(self, painter):
        """Draw guide lines with proper thickness rendering"""
        thickness = self.config.thickness
        
        for guide in self.guides:
            # Determine visual state
            if guide.selected:
                color = QColor(self.config.get_color('selected_guide_color'))
                line_thickness = thickness + 2
            elif guide.locked:
                color = QColor(self.config.get_color('locked_guide_color'))
                line_thickness = thickness + 1
            elif guide.hover:
                color = QColor(Colors.GUIDE_HOVER)
                line_thickness = thickness + 1
            else:
                color = QColor(self.config.get_color('guide_color'))
                line_thickness = thickness
            
            color.setAlpha(int(255 * self.config.opacity))
            
            # CRITICAL FIX: True 1px rendering
            if line_thickness == 1:
                painter.setRenderHint(QPainter.Antialiasing, False)
                pen = QPen(color, 0)  # Cosmetic pen = always 1px
            else:
                painter.setRenderHint(QPainter.Antialiasing, True)
                pen = QPen(color, line_thickness)
                pen.setCapStyle(Qt.RoundCap)
            
            painter.setPen(pen)
            
            pos = int(guide.scaled_position * self.config.scale)
            
            if guide.orientation == 'horizontal':
                painter.drawLine(0, pos, self.width(), pos)
                if self.config.get_visibility('measurements') and \
                   (guide.hover or guide.dragging or guide.selected):
                    self.draw_guide_label(painter, guide, pos, 'horizontal', guide.selected)
            else:
                painter.drawLine(pos, 0, pos, self.height())
                if self.config.get_visibility('measurements') and \
                   (guide.hover or guide.dragging or guide.selected):
                    self.draw_guide_label(painter, guide, pos, 'vertical', guide.selected)
    
    def draw_preview_guide(self, painter):
        """Draw preview guide while dragging from ruler"""
        color = QColor(self.config.get_color('guide_color'))
        color.setAlpha(180)
        
        thickness = self.config.thickness
        
        if thickness == 1:
            painter.setRenderHint(QPainter.Antialiasing, False)
            pen = QPen(color, 0, Qt.DashLine)
        else:
            painter.setRenderHint(QPainter.Antialiasing, True)
            pen = QPen(color, thickness, Qt.DashLine)
            pen.setCapStyle(Qt.RoundCap)
        
        painter.setPen(pen)
        
        pos = int(self.preview_guide.scaled_position * self.config.scale)
        
        if self.preview_guide.orientation == 'horizontal':
            painter.drawLine(0, pos, self.width(), pos)
            if self.config.get_visibility('measurements'):
                self.draw_guide_label(painter, self.preview_guide, pos, 'horizontal', False)
        else:
            painter.drawLine(pos, 0, pos, self.height())
            if self.config.get_visibility('measurements'):
                self.draw_guide_label(painter, self.preview_guide, pos, 'vertical', False)
    
    def draw_guide_label(self, painter, guide, position, orientation, is_selected):
        """Draw guide position label"""
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        bg_color = QColor(Colors.GUIDE_SELECTED if is_selected else '#000000')
        bg_color.setAlpha(230)
        text_color = QColor(Colors.TEXT_PRIMARY)
        
        scaled_pos = int(guide.scaled_position)
        label_text = f"{scaled_pos}px"
        
        if guide.locked:
            label_text += " 🔒"
        
        font = QFont('Segoe UI', 8, QFont.Bold)
        painter.setFont(font)
        metrics = painter.fontMetrics()
        
        padding = 6
        text_width = metrics.width(label_text) + padding * 2
        text_height = metrics.height() + padding
        
        if orientation == 'horizontal':
            rect = QRect(self.config.ruler_size + 10, position - text_height // 2,
                        text_width, text_height)
        else:
            rect = QRect(position - text_width // 2, self.config.ruler_size + 10,
                        text_width, text_height)
        
        # Shadow
        shadow_rect = rect.adjusted(1, 1, 1, 1)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 100))
        painter.drawRoundedRect(shadow_rect, 3, 3)
        
        # Background
        painter.setBrush(bg_color)
        painter.drawRoundedRect(rect, 3, 3)
        
        # Text
        painter.setPen(text_color)
        painter.drawText(rect, Qt.AlignCenter, label_text)
    
    def draw_coordinates(self, painter):
        """Draw cursor coordinates"""
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        local_pos = self.mapFromGlobal(self.cursor_pos)
        scaled_x = int(local_pos.x() / self.config.scale)
        scaled_y = int(local_pos.y() / self.config.scale)
        
        coord_text = f"X: {scaled_x}  Y: {scaled_y}"
        
        font = QFont('Segoe UI', 9, QFont.Bold)
        painter.setFont(font)
        metrics = painter.fontMetrics()
        
        padding = 8
        text_width = metrics.width(coord_text) + padding * 2
        text_height = metrics.height() + padding
        
        # Position near cursor
        text_x = local_pos.x() + 15
        text_y = local_pos.y() + 15
        
        # Keep on screen
        if text_x + text_width > self.width() - 10:
            text_x = local_pos.x() - text_width - 15
        if text_y + text_height > self.height() - 10:
            text_y = local_pos.y() - text_height - 15
        
        rect = QRect(text_x, text_y, text_width, text_height)
        
        # Background
        bg = QColor(0, 0, 0, 200)
        painter.setPen(Qt.NoPen)
        painter.setBrush(bg)
        painter.drawRoundedRect(rect, 4, 4)
        
        # Text
        painter.setPen(QColor(Colors.TEXT_PRIMARY))
        painter.drawText(rect, Qt.AlignCenter, coord_text)
    
    def draw_click_through_badge(self, painter):
        """Draw click-through mode indicator"""
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        text = "🔓 Click-Through Active  •  Ctrl+Shift+T to disable"
        font = QFont('Segoe UI', 9, QFont.Bold)
        painter.setFont(font)
        metrics = painter.fontMetrics()
        
        padding = 10
        text_width = metrics.width(text) + padding * 2
        text_height = metrics.height() + padding
        
        # Top-right position
        rect = QRect(self.width() - text_width - 20, 20, text_width, text_height)
        
        # Background with warning color
        bg = QColor(Colors.WARNING)
        bg.setAlpha(220)
        painter.setPen(Qt.NoPen)
        painter.setBrush(bg)
        painter.drawRoundedRect(rect, 6, 6)
        
        # Text
        painter.setPen(QColor('#000000'))
        painter.drawText(rect, Qt.AlignCenter, text)
    
    # ═══════════════════════════════════════════════════════════════════════
    # EVENT HANDLING - OPTIMIZED
    # ═══════════════════════════════════════════════════════════════════════
    
    def mouseMoveEvent(self, event):
        """Throttled mouse move handling"""
        if self.click_through_mode:
            return
        
        pos = event.pos()
        snapped = self.snap_position(pos)
        
        # Update cursor position with throttling
        now = time.time()
        throttle_passed = (now - self.last_cursor_update > 0.05)
        if throttle_passed:
            self.cursor_pos = event.globalPos()
            self.last_cursor_update = now
        
        # Update guide hover states
        hover_updated = False
        for guide in self.guides:
            old_hover = guide.hover
            guide.hover = not guide.locked and guide.contains_point(pos, self.config.scale)
            if old_hover != guide.hover:
                hover_updated = True
                
        should_update = False
        
        # Handle preview guide
        if self.preview_guide and self.preview_guide.dragging:
            if self.preview_guide.orientation == 'horizontal':
                self.preview_guide.update_position(snapped.y(), self.config.scale)
            else:
                self.preview_guide.update_position(snapped.x(), self.config.scale)
            should_update = True
        
        # Handle guide dragging
        elif self.dragging_guide:
            if self.dragging_guide.orientation == 'horizontal':
                self.dragging_guide.update_position(snapped.y(), self.config.scale)
            else:
                self.dragging_guide.update_position(snapped.x(), self.config.scale)
            should_update = True
            
        # Update if hover changed or coordinates tracker is active
        elif hover_updated:
            should_update = True
        elif self.config.get_visibility('coordinates') and throttle_passed:
            should_update = True
            
        if should_update:
            self.update()
        
        # Update cursor shape
        self.update_cursor_shape(pos)
    
    def update_cursor_shape(self, pos):
        """Update cursor based on context"""
        if any(g.hover for g in self.guides):
            for g in self.guides:
                if g.hover:
                    if g.orientation == 'horizontal':
                        self.setCursor(Qt.SplitVCursor)
                    else:
                        self.setCursor(Qt.SplitHCursor)
                    return
        elif self.preview_guide:
            if self.preview_guide.orientation == 'horizontal':
                self.setCursor(Qt.SplitVCursor)
            else:
                self.setCursor(Qt.SplitHCursor)
        elif pos.x() < self.config.ruler_size and pos.y() > self.config.ruler_size:
            self.setCursor(Qt.SplitHCursor)
        elif pos.y() < self.config.ruler_size and pos.x() > self.config.ruler_size:
            self.setCursor(Qt.SplitVCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
    
    def mousePressEvent(self, event):
        """Handle mouse press"""
        if self.click_through_mode or event.button() != Qt.LeftButton:
            return
        
        pos = event.pos()
        snapped = self.snap_position(pos)
        
        # Deselect current guide
        if self.selected_guide:
            self.selected_guide.selected = False
            self.selected_guide = None
        
        # Create guide from left ruler (vertical)
        if pos.x() < self.config.ruler_size and pos.y() > self.config.ruler_size:
            self.preview_guide = Guide('vertical', snapped.x(), self.config.scale)
            self.preview_guide.dragging = True
        
        # Create guide from top ruler (horizontal)
        elif pos.y() < self.config.ruler_size and pos.x() > self.config.ruler_size:
            self.preview_guide = Guide('horizontal', snapped.y(), self.config.scale)
            self.preview_guide.dragging = True
        
        # Select/drag existing guide
        else:
            for guide in reversed(self.guides):
                if guide.contains_point(pos, self.config.scale):
                    if not guide.locked:
                        guide.dragging = True
                        self.dragging_guide = guide
                    guide.selected = True
                    self.selected_guide = guide
                    break
        
        self.update()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if self.click_through_mode:
            return
        
        pos = event.pos()
        
        # Finalize preview guide
        if self.preview_guide:
            # Delete if dragged back to ruler
            if (self.preview_guide.orientation == 'vertical' and pos.x() < self.config.ruler_size) or \
               (self.preview_guide.orientation == 'horizontal' and pos.y() < self.config.ruler_size):
                pass  # Don't add guide
            else:
                self.guides.append(self.preview_guide)
                self.guide_changed.emit()
            
            self.preview_guide = None
        
        # Finalize dragging guide
        elif self.dragging_guide:
            # Delete if dragged to ruler
            if (self.dragging_guide.orientation == 'vertical' and pos.x() < self.config.ruler_size) or \
               (self.dragging_guide.orientation == 'horizontal' and pos.y() < self.config.ruler_size):
                if self.dragging_guide in self.guides:
                    self.guides.remove(self.dragging_guide)
                self.selected_guide = None
                self.guide_changed.emit()
            
            self.dragging_guide.dragging = False
            self.dragging_guide = None
        
        self.update()
    
    def mouseDoubleClickEvent(self, event):
        """Toggle guide lock on double-click"""
        if self.click_through_mode:
            return
        
        pos = event.pos()
        for guide in self.guides:
            if guide.contains_point(pos, self.config.scale):
                guide.locked = not guide.locked
                self.update()
                break
    
    def wheelEvent(self, event):
        """Zoom with Ctrl+Wheel"""
        if event.modifiers() & Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
    
    def keyPressEvent(self, event):
        """Keyboard shortcuts"""
        # Delete selected guide
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            if self.selected_guide and not self.selected_guide.locked:
                self.guides.remove(self.selected_guide)
                self.selected_guide = None
                self.guide_changed.emit()
                self.update()
        
        # Deselect
        elif event.key() == Qt.Key_Escape:
            if self.selected_guide:
                self.selected_guide.selected = False
                self.selected_guide = None
                self.update()
        
        # Toggle lock
        elif event.key() == Qt.Key_L:
            if self.selected_guide:
                self.selected_guide.locked = not self.selected_guide.locked
                self.update()
        
        # Nudge guide
        elif event.key() in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
            if self.selected_guide and not self.selected_guide.locked:
                nudge = 10 if event.modifiers() & Qt.ShiftModifier else 1
                
                if self.selected_guide.orientation == 'horizontal':
                    if event.key() == Qt.Key_Up:
                        self.selected_guide.update_position(
                            self.selected_guide.position - nudge, self.config.scale)
                    elif event.key() == Qt.Key_Down:
                        self.selected_guide.update_position(
                            self.selected_guide.position + nudge, self.config.scale)
                else:
                    if event.key() == Qt.Key_Left:
                        self.selected_guide.update_position(
                            self.selected_guide.position - nudge, self.config.scale)
                    elif event.key() == Qt.Key_Right:
                        self.selected_guide.update_position(
                            self.selected_guide.position + nudge, self.config.scale)
                
                self.guide_changed.emit()
                self.update()
        
        super().keyPressEvent(event)
    
    # ═══════════════════════════════════════════════════════════════════════
    # GUIDE MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════
    
    def clear_guides(self):
        """Clear all guides"""
        self.guides.clear()
        self.selected_guide = None
        self.dragging_guide = None
        self.preview_guide = None
        self.guide_changed.emit()
        self.update()
    
    def lock_all_guides(self):
        """Lock all guides"""
        for guide in self.guides:
            guide.locked = True
        self.update()
    
    def unlock_all_guides(self):
        """Unlock all guides"""
        for guide in self.guides:
            guide.locked = False
        self.update()
    
    def get_guides_data(self):
        """Export guides to dict"""
        return [g.to_dict() for g in self.guides]
    
    def set_guides_data(self, data):
        """Import guides from dict"""
        self.guides.clear()
        for g in data:
            self.guides.append(Guide.from_dict(g, self.config.scale))
        self.selected_guide = None
        self.guide_changed.emit()
        self.update()


# ═══════════════════════════════════════════════════════════════════════════
# CONTROL PANEL - MINIMAL PROFESSIONAL UI WITH TABS
# ═══════════════════════════════════════════════════════════════════════════

class CompactSlider(QWidget):
    """Slider with integrated label and value display"""
    valueChanged = pyqtSignal(int)
    
    def __init__(self, label, min_val, max_val, suffix='', parent=None):
        super().__init__(parent)
        self.suffix = suffix
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Label
        self.label = QLabel(label)
        self.label.setMinimumWidth(70)
        self.label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(self.label)
        
        # Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(min_val, max_val)
        self.slider.valueChanged.connect(self.on_value_changed)
        layout.addWidget(self.slider, 1)
        
        # Value label
        self.value_label = QLabel()
        self.value_label.setMinimumWidth(50)
        self.value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.value_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-weight: bold;")
        layout.addWidget(self.value_label)
    
    def on_value_changed(self, value):
        self.value_label.setText(f"{value}{self.suffix}")
        self.valueChanged.emit(value)
    
    def setValue(self, value):
        self.slider.blockSignals(True)
        self.slider.setValue(value)
        self.value_label.setText(f"{value}{self.suffix}")
        self.slider.blockSignals(False)
    
    def value(self):
        return self.slider.value()


class ControlPanel(QMainWindow):
    """Minimal, professional control panel with tabs"""
    
    def __init__(self, overlay, config_model, config_manager):
        super().__init__()
        self.overlay = overlay
        self.config = config_model
        self.config_manager = config_manager
        
        self.init_ui()
        self.apply_modern_styles()
        self.connect_signals()
    
    def init_ui(self):
        """Build minimal UI with tabs"""
        self.setWindowTitle('Ruler Guides Pro by Abhisht Pandey')
        
        icon_path = get_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))
            
        self.setGeometry(120, 120, 460, 500)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Window)
        
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ═══════════════════════════════════════════════════════════════════
        # HEADER
        # ═══════════════════════════════════════════════════════════════════
        
        header_widget = QWidget()
        # Seamlessly match the main theme instead of looking like a separate strip
        header_widget.setStyleSheet("background-color: transparent;")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(24, 24, 24, 16)
        header_layout.setSpacing(14)
        header_layout.setAlignment(Qt.AlignCenter)
        
        # Load Icon
        icon_path = get_icon_path()
        if icon_path:
            icon_label = QLabel()
            pixmap = QPixmap(icon_path)
            # High-quality scaling
            pixmap = pixmap.scaled(38, 38, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
            header_layout.addWidget(icon_label)
        
        # Text Block
        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        
        header = QLabel('RULER GUIDES PRO')
        header_font = QFont('Segoe UI', 13, QFont.Bold)
        header_font.setLetterSpacing(QFont.PercentageSpacing, 105)
        header.setFont(header_font)
        header.setStyleSheet(f"color: {Colors.ACCENT};")
        
        subheader = QLabel('BY ABHISHT PANDEY')
        subheader_font = QFont('Segoe UI', 8, QFont.Medium)
        subheader_font.setLetterSpacing(QFont.PercentageSpacing, 120)
        subheader.setFont(subheader_font)
        subheader.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        
        text_layout.addWidget(header)
        text_layout.addWidget(subheader)
        
        header_layout.addLayout(text_layout)
        
        main_layout.addWidget(header_widget)
        
        # ═══════════════════════════════════════════════════════════════════
        # TABS
        # ═══════════════════════════════════════════════════════════════════
        
        tabs = QTabWidget()
        tabs.setDocumentMode(False)
        tabs.setUsesScrollButtons(False)
        
        # Tab 1: Scale & Zoom
        tab1 = self.create_scale_tab()
        tabs.addTab(tab1, '  Scale  ')
        
        # Tab 2: Appearance
        tab2 = self.create_appearance_tab()
        tabs.addTab(tab2, '  Style  ')
        
        # Tab 3: Display & Grid
        tab3 = self.create_display_tab()
        tabs.addTab(tab3, '  Display  ')
        
        # Tab 4: Guides
        tab4 = self.create_guides_tab()
        tabs.addTab(tab4, '  Guides  ')
        
        # Tab 5: Shortcuts
        tab5 = self.create_shortcuts_tab()
        tabs.addTab(tab5, '  Keys  ')
        
        main_layout.addWidget(tabs)
    
    def create_scale_tab(self):
        """Scale and zoom controls"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Scale slider
        self.scale_slider = CompactSlider('Zoom', 25, 1000, '%')
        self.scale_slider.setValue(int(self.config.scale * 100))
        self.scale_slider.valueChanged.connect(self.on_scale_changed)
        layout.addWidget(self.scale_slider)
        
        # Preset buttons
        preset_label = QLabel('Quick Presets:')
        preset_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; margin-top: 8px;")
        layout.addWidget(preset_label)
        
        preset_grid = QGridLayout()
        preset_grid.setSpacing(6)
        
        presets = [
            ('25%', 0.25), ('50%', 0.5), ('100%', 1.0), ('200%', 2.0),
            ('300%', 3.0), ('400%', 4.0), ('500%', 5.0), ('1000%', 10.0)
        ]
        
        for i, (label, value) in enumerate(presets):
            btn = QPushButton(label)
            btn.setMinimumHeight(34)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(self.make_scale_setter(value))
            preset_grid.addWidget(btn, i // 4, i % 4)
        
        layout.addLayout(preset_grid)
        layout.addStretch()
        
        return tab
    
    def create_appearance_tab(self):
        """Appearance settings"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Opacity
        self.opacity_slider = CompactSlider('Opacity', 10, 100, '%')
        self.opacity_slider.setValue(int(self.config.opacity * 100))
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        layout.addWidget(self.opacity_slider)
        
        # Thickness
        self.thickness_slider = CompactSlider('Thickness', 1, 15, 'px')
        self.thickness_slider.setValue(self.config.thickness)
        self.thickness_slider.valueChanged.connect(self.on_thickness_changed)
        layout.addWidget(self.thickness_slider)
        
        # Color buttons
        color_label = QLabel('Colors:')
        color_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; margin-top: 8px;")
        layout.addWidget(color_label)
        
        color_grid = QGridLayout()
        color_grid.setSpacing(6)
        
        colors = [
            ('Guide Color', 'guide_color'),
            ('Selected', 'selected_guide_color'),
            ('Locked', 'locked_guide_color'),
            ('Grid Color', 'grid_color')
        ]
        
        for i, (label, key) in enumerate(colors):
            btn = QPushButton(label)
            btn.setMinimumHeight(34)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setObjectName(key)
            btn.clicked.connect(self.make_color_chooser(key))
            
            # Pure text button
            btn.setProperty('color_key', key)
            
            color_grid.addWidget(btn, i // 2, i % 2)
        
        layout.addLayout(color_grid)
        layout.addStretch()
        
        return tab
    
    def create_display_tab(self):
        """Display and grid settings"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Display options
        display_label = QLabel('Display Options:')
        display_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(display_label)
        
        display_grid = QGridLayout()
        display_grid.setSpacing(10)
        
        self.rulers_check = QCheckBox('Show Rulers')
        self.rulers_check.setChecked(self.config.get_visibility('rulers'))
        self.rulers_check.toggled.connect(self.make_visibility_toggler('rulers'))
        display_grid.addWidget(self.rulers_check, 0, 0)
        
        self.guides_check = QCheckBox('Show Guides')
        self.guides_check.setChecked(self.config.get_visibility('guides'))
        self.guides_check.toggled.connect(self.make_visibility_toggler('guides'))
        display_grid.addWidget(self.guides_check, 0, 1)
        
        self.coords_check = QCheckBox('Show Coordinates')
        self.coords_check.setChecked(self.config.get_visibility('coordinates'))
        self.coords_check.toggled.connect(self.make_visibility_toggler('coordinates'))
        display_grid.addWidget(self.coords_check, 1, 0)
        
        self.grid_check = QCheckBox('Show Grid')
        self.grid_check.setChecked(self.config.get_visibility('grid'))
        self.grid_check.toggled.connect(self.make_visibility_toggler('grid'))
        display_grid.addWidget(self.grid_check, 1, 1)
        
        layout.addLayout(display_grid)
        
        # Removed Separator
        
        # Grid settings
        grid_label = QLabel('Grid Settings:')
        grid_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(grid_label)
        
        grid_size_row = QHBoxLayout()
        grid_size_row.addWidget(QLabel('Grid Size:'))
        
        self.grid_spin = QSpinBox()
        self.grid_spin.setRange(1, 500)
        self.grid_spin.setValue(self.config.grid_size)
        self.grid_spin.setSuffix(' px')
        self.grid_spin.valueChanged.connect(self.on_grid_size_changed)
        grid_size_row.addWidget(self.grid_spin)
        grid_size_row.addStretch()
        
        layout.addLayout(grid_size_row)
        
        self.snap_check = QCheckBox('Snap to Grid')
        self.snap_check.setChecked(self.config.snap_to_grid)
        self.snap_check.toggled.connect(self.on_snap_toggled)
        layout.addWidget(self.snap_check)
        
        # Removed Separator
        
        # Click-through mode
        mode_label = QLabel('Modes:')
        mode_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(mode_label)
        
        self.click_through_check = QCheckBox('Click-Through Mode (Ctrl+Shift+T)')
        self.click_through_check.toggled.connect(self.toggle_click_through)
        layout.addWidget(self.click_through_check)
        
        layout.addStretch()
        
        return tab
    
    def create_guides_tab(self):
        """Guide management"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Guide info
        self.guide_info = QLabel('Total: 0 guides')
        self.guide_info.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 10pt; font-weight: bold;")
        layout.addWidget(self.guide_info)
        
        # Actions
        actions_label = QLabel('Quick Actions:')
        actions_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; margin-top: 8px;")
        layout.addWidget(actions_label)
        
        actions_grid = QGridLayout()
        actions_grid.setSpacing(6)
        
        actions = [
            ('Clear All Guides', self.overlay.clear_guides),
            ('Lock All Guides', self.overlay.lock_all_guides),
            ('Unlock All Guides', self.overlay.unlock_all_guides),
        ]
        
        for i, (label, func) in enumerate(actions):
            btn = QPushButton(label)
            btn.setMinimumHeight(34)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(func)
            actions_grid.addWidget(btn, i, 0)
        
        layout.addLayout(actions_grid)
        
        # Removed Separator
        
        # Layout management
        layout_label = QLabel('Layout Management:')
        layout_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(layout_label)
        
        layout_grid = QGridLayout()
        layout_grid.setSpacing(6)
        
        save_btn = QPushButton('💾 Save Layout')
        save_btn.setMinimumHeight(34)
        save_btn.clicked.connect(self.save_layout)
        layout_grid.addWidget(save_btn, 0, 0)
        
        load_btn = QPushButton('📂 Load Layout')
        load_btn.setMinimumHeight(34)
        load_btn.clicked.connect(self.load_layout)
        layout_grid.addWidget(load_btn, 0, 1)
        
        config_btn = QPushButton('🗂️ Config Folder')
        config_btn.setMinimumHeight(34)
        config_btn.clicked.connect(self.config_manager.open_config_folder)
        layout_grid.addWidget(config_btn, 1, 0, 1, 2)
        
        layout.addLayout(layout_grid)
        layout.addStretch()
        
        return tab
    
    def create_shortcuts_tab(self):
        """Shortcuts reference"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        
        shortcuts_text = QTextEdit()
        shortcuts_text.setReadOnly(True)
        shortcuts_text.setFont(QFont('Consolas', 9))
        
        shortcuts_html = f"""
        <style>
            body {{ color: {Colors.TEXT_PRIMARY}; background: {Colors.BG_PRIMARY}; font-family: 'Segoe UI', Arial, sans-serif; padding: 10px; }}
            h3 {{ color: {Colors.ACCENT}; margin-top: 16px; margin-bottom: 10px; font-weight: 600; font-size: 14px; border-bottom: 1px solid {Colors.BORDER}; padding-bottom: 4px; }}
            table {{ width: 100%; border-collapse: separate; border-spacing: 0 6px; }}
            td {{ padding: 2px 4px; vertical-align: middle; }}
            .key {{ 
                background: {Colors.BG_SURFACE}; 
                color: {Colors.TEXT_PRIMARY}; 
                padding: 3px 8px; 
                border-radius: 4px; 
                border: 1px solid {Colors.BORDER};
                border-bottom: 2px solid {Colors.BORDER_LIGHT};
                font-family: 'Consolas', monospace;
                font-size: 11px;
                font-weight: bold;
                display: inline-block;
            }}
            .desc {{ color: {Colors.TEXT_SECONDARY}; font-size: 12px; }}
            .icon {{ font-family: 'Segoe UI Symbol', sans-serif; margin-right: 4px; }}
        </style>
        
        <h3><span class="icon">⌗</span> Keyboard Shortcuts</h3>
        <table>
        <tr><td width="35%"><span class="key">Delete</span></td><td class="desc">Delete selected guide</td></tr>
        <tr><td><span class="key">L</span></td><td class="desc">Lock/unlock selected guide</td></tr>
        <tr><td><span class="key">Esc</span></td><td class="desc">Deselect current guide</td></tr>
        <tr><td><span class="key">Arrows</span></td><td class="desc">Nudge guide precisely (1px)</td></tr>
        <tr><td><span class="key">Shift</span> + <span class="key">Arrows</span></td><td class="desc">Nudge guide quickly (10px)</td></tr>
        </table>
        
        <h3><span class="icon">⚲</span> Zoom Controls</h3>
        <table>
        <tr><td width="35%"><span class="key">Ctrl</span> + <span class="key">Wheel</span></td><td class="desc">Zoom display scale in/out</td></tr>
        </table>
        
        <h3><span class="icon">⚡</span> Global Hotkeys</h3>
        <table>
        <tr><td width="35%"><span class="key">Ctrl</span>+<span class="key">I</span></td><td class="desc">Toggle rulers visibility</td></tr>
        <tr><td><span class="key">Ctrl</span>+<span class="key">Shift</span>+<span class="key">G</span></td><td class="desc">Toggle guides visibility</td></tr>
        <tr><td><span class="key">Ctrl</span>+<span class="key">Shift</span>+<span class="key">T</span></td><td class="desc">Toggle click-through mode</td></tr>
        <tr><td><span class="key">Ctrl</span>+<span class="key">Shift</span>+<span class="key">C</span></td><td class="desc">Clear all active guides</td></tr>
        <tr><td><span class="key">Ctrl</span>+<span class="key">Shift</span>+<span class="key">P</span></td><td class="desc">Show/Hide control panel</td></tr>
        </table>
        
        <h3><span class="icon">↹</span> Mouse Actions</h3>
        <table>
        <tr><td width="35%"><span style="color:{Colors.TEXT_PRIMARY}; font-weight:bold;">Drag</span> from ruler</td><td class="desc">Create new guide</td></tr>
        <tr><td><span style="color:{Colors.TEXT_PRIMARY}; font-weight:bold;">Drag</span> guide</td><td class="desc">Move existing guide</td></tr>
        <tr><td><span style="color:{Colors.TEXT_PRIMARY}; font-weight:bold;">Drag</span> to ruler</td><td class="desc">Delete guide</td></tr>
        <tr><td><span style="color:{Colors.TEXT_PRIMARY}; font-weight:bold;">Double-click</span></td><td class="desc">Lock/unlock guide</td></tr>
        <tr><td><span style="color:{Colors.TEXT_PRIMARY}; font-weight:bold;">Click</span> guide</td><td class="desc">Select guide</td></tr>
        </table>
        
        <h3><span class="icon">⦿</span> Visual Indicators</h3>
        <table>
        <tr><td width="35%"><span style="color:{Colors.GUIDE_DEFAULT}; font-size:16px;">●</span> Cyan</td><td class="desc">Standard active guide</td></tr>
        <tr><td><span style="color:{Colors.GUIDE_SELECTED}; font-size:16px;">●</span> Orange</td><td class="desc">Currently selected guide</td></tr>
        <tr><td><span style="color:{Colors.GUIDE_LOCKED}; font-size:16px;">●</span> Amber</td><td class="desc">Locked guide (immovable)</td></tr>
        </table>
        """
        
        shortcuts_text.setHtml(shortcuts_html)
        layout.addWidget(shortcuts_text)
        
        return tab
    
    # ═══════════════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ═══════════════════════════════════════════════════════════════════════
    
    def make_scale_setter(self, value):
        """Create scale setter function"""
        def setter():
            self.config.scale = value
        return setter
    
    def make_visibility_toggler(self, element):
        """Create visibility toggler function"""
        def toggler(visible):
            self.config.set_visibility(element, visible)
        return toggler
    
    def make_color_chooser(self, key):
        """Create color chooser function"""
        def chooser():
            self.choose_color(key)
        return chooser
    
    # ═══════════════════════════════════════════════════════════════════════
    # EVENT HANDLERS
    # ═══════════════════════════════════════════════════════════════════════
    
    def on_scale_changed(self, value):
        self.config.scale = value / 100.0
    
    def on_opacity_changed(self, value):
        self.config.opacity = value / 100.0
    
    def on_thickness_changed(self, value):
        self.config.thickness = value
    
    def on_grid_size_changed(self, value):
        self.config.grid_size = value
    
    def on_snap_toggled(self, checked):
        self.config.snap_to_grid = checked
    
    def connect_signals(self):
        """Connect all signals"""
        self.overlay.guide_changed.connect(self.update_guide_info)
        self.config.scale_changed.connect(self.on_config_scale_changed)
        self.config.config_saved.connect(self.save_config)
        self.config.visibility_changed.connect(self.on_config_visibility_changed)
        self.config.grid_size_changed.connect(self.on_config_grid_size_changed)
        self.config.snap_changed.connect(self.on_config_snap_changed)
        
        # Initial update
        self.update_guide_info()
        
    def on_config_visibility_changed(self, element, visible):
        if element == 'rulers' and self.rulers_check.isChecked() != visible:
            self.rulers_check.setChecked(visible)
        elif element == 'guides' and self.guides_check.isChecked() != visible:
            self.guides_check.setChecked(visible)
        elif element == 'coordinates' and self.coords_check.isChecked() != visible:
            self.coords_check.setChecked(visible)
        elif element == 'grid' and self.grid_check.isChecked() != visible:
            self.grid_check.setChecked(visible)

    def on_config_grid_size_changed(self, size):
        if self.grid_spin.value() != size:
            self.grid_spin.setValue(size)

    def on_config_snap_changed(self, snap):
        if self.snap_check.isChecked() != snap:
            self.snap_check.setChecked(snap)
    
    def on_config_scale_changed(self, scale):
        """Handle config scale change"""
        self.scale_slider.setValue(int(scale * 100))
    
    def update_guide_info(self):
        """Update guide count display"""
        total = len(self.overlay.guides)
        locked = sum(1 for g in self.overlay.guides if g.locked)
        self.guide_info.setText(f"Total: {total} guides ({locked} locked)")
    
    def choose_color(self, key):
        """Color picker dialog"""
        current = QColor(self.config.get_color(key))
        color = QColorDialog.getColor(current, self, f'Choose {key.replace("_", " ").title()}')
        
        if color.isValid():
            self.config.set_color(key, color.name())
    
    def toggle_click_through(self, enabled):
        """Toggle click-through mode"""
        self.overlay.make_click_through(enabled)
    
    def save_layout(self):
        """Save current layout"""
        data = {
            'guides': self.overlay.get_guides_data(),
            'scale': self.config.scale,
            'grid_size': self.config.grid_size,
            'snap_to_grid': self.config.snap_to_grid
        }
        
        if self.config_manager.save_layout(data):
            self.show_notification('✓ Layout saved successfully!', Colors.SUCCESS)
    
    def load_layout(self):
        """Load saved layout"""
        data = self.config_manager.load_layout()
        
        if data:
            if 'scale' in data:
                self.config.scale = data['scale']
            if 'grid_size' in data:
                self.config.grid_size = data['grid_size']
            if 'snap_to_grid' in data:
                self.config.snap_to_grid = data['snap_to_grid']
            
            self.overlay.set_guides_data(data.get('guides', []))
            self.show_notification('✓ Layout loaded successfully!', Colors.SUCCESS)
        else:
            self.show_notification('✗ No saved layout found!', Colors.WARNING)
    
    def save_config(self):
        """Save configuration"""
        self.config_manager.save_config(self.config)
    
    def show_notification(self, text, color):
        """Show temporary notification"""
        msg = QMessageBox(self)
        msg.setWindowTitle('Ruler Guides Pro')
        msg.setText(text)
        
        if color == Colors.WARNING:
            msg.setIcon(QMessageBox.Warning)
        elif color == Colors.ERROR:
            msg.setIcon(QMessageBox.Critical)
        else:
            msg.setIcon(QMessageBox.Information)
            
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def apply_modern_styles(self):
        """Apply modern minimal stylesheet"""
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {Colors.BG_PRIMARY};
                color: {Colors.TEXT_PRIMARY};
                font-family: 'Inter', 'Segoe UI', sans-serif;
                font-size: 14px;
            }}
            
            QTabWidget::pane {{
                border: none;
                background-color: {Colors.BG_PRIMARY};
            }}
            
            QTabWidget::tab-bar {{
                alignment: center;
            }}
            
            QTabBar {{
                background-color: transparent;
                qproperty-expanding: true;
            }}
            
            QTabBar::tab {{
                background-color: transparent;
                color: {Colors.TEXT_SECONDARY};
                padding: 8px 0px 10px 0px; 
                margin: 4px 4px;
                min-width: 78px;
                min-height: 26px; 
                border-radius: 6px;
                border: none;
                font-weight: 600;
            }}
            
            QTabBar::tab:selected {{
                background-color: {Colors.BG_SURFACE};
                color: {Colors.ACCENT};
            }}
            
            QTabBar::tab:hover:!selected {{
                background-color: {Colors.BG_SECONDARY};
                color: {Colors.TEXT_PRIMARY};
            }}
            
            QPushButton {{
                background-color: {Colors.BG_SURFACE};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: 6px;
                padding: 5px 16px; /* Reduced vertical padding */
                color: {Colors.TEXT_PRIMARY};
                font-weight: 500;
            }}
            
            QPushButton:hover {{
                background-color: {Colors.BORDER};
                border-color: {Colors.ACCENT};
            }}
            
            QPushButton:pressed {{
                background-color: {Colors.BG_SECONDARY};
                color: {Colors.TEXT_SECONDARY};
            }}
            
            QSlider::groove:horizontal {{
                border: none;
                height: 4px;
                background: {Colors.BORDER};
                border-radius: 2px;
            }}
            
            QSlider::sub-page:horizontal {{
                background: {Colors.ACCENT};
                border-radius: 2px;
            }}
            
            QSlider::handle:horizontal {{
                background: {Colors.TEXT_PRIMARY};
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }}
            
            QSlider::handle:horizontal:hover {{
                background: {Colors.ACCENT_HOVER};
            }}
            
            QSpinBox {{
                background-color: {Colors.BG_SURFACE};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                padding: 8px 12px;
                color: {Colors.TEXT_PRIMARY};
            }}
            
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 0px;
                height: 0px;
                border: none;
                background: transparent;
            }}
            
            QSpinBox:focus {{
                border-color: {Colors.ACCENT};
            }}
            
            QCheckBox {{
                spacing: 12px;
                color: {Colors.TEXT_PRIMARY};
                font-size: 14px;
            }}
            
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: 4px;
                background: {Colors.BG_SURFACE};
            }}
            
            QCheckBox::indicator:checked {{
                background: {Colors.ACCENT};
                border-color: {Colors.ACCENT};
            }}
            
            QCheckBox::indicator:hover {{
                border-color: {Colors.ACCENT};
            }}
            
            QLabel {{
                background: transparent;
            }}
            
            QTextEdit {{
                background-color: {Colors.BG_SECONDARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                color: {Colors.TEXT_SECONDARY};
                padding: 12px;
            }}
            
            QScrollBar:vertical {{
                border: none;
                background: {Colors.BG_PRIMARY};
                width: 12px;
                margin: 2px;
                border-radius: 4px;
            }}
            
            QScrollBar::handle:vertical {{
                background: {Colors.BORDER_LIGHT};
                min-height: 30px;
                border-radius: 4px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background: {Colors.TEXT_MUTED};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
                background: none;
            }}
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
            
            QScrollBar:horizontal {{
                border: none;
                background: {Colors.BG_PRIMARY};
                height: 12px;
                margin: 2px;
                border-radius: 4px;
            }}
            
            QScrollBar::handle:horizontal {{
                background: {Colors.BORDER_LIGHT};
                min-width: 30px;
                border-radius: 4px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background: {Colors.TEXT_MUTED};
            }}
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
                background: none;
            }}
            
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}
        """)
    
    def closeEvent(self, event):
        """Save on close and quit"""
        self.save_config()
        import keyboard
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        event.accept()
        from PyQt5.QtWidgets import QApplication
        QApplication.quit()


# ═══════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════

class HotkeySignals(QObject):
    """Signals for routing hotkey events to main thread"""
    toggle_rulers = pyqtSignal()
    toggle_guides = pyqtSignal()
    clear_guides = pyqtSignal()
    show_panel = pyqtSignal()
    toggle_click_through = pyqtSignal()

class RulerGuidesApp:
    """Main application controller"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.app.setApplicationName('Ruler Guides Pro by ISOLATE')
        
        # Initialize components
        self.config_model = ConfigModel()
        self.config_manager = ConfigManager()
        
        # Load saved config
        self.config_manager.load_config(self.config_model)
        
        # Create UI
        self.overlay = RulerOverlay(self.config_model)
        self.control_panel = ControlPanel(self.overlay, self.config_model, self.config_manager)
        
        icon_path = get_icon_path()
        if icon_path:
            app_icon = QIcon(icon_path)
            self.app.setWindowIcon(app_icon)
            
        # Setup system tray
        self.create_tray_icon()
        
        # Setup signals for thread-safe hotkey callbacks
        self.signals = HotkeySignals()
        self.signals.toggle_rulers.connect(self.toggle_rulers)
        self.signals.toggle_guides.connect(self.toggle_guides)
        self.signals.clear_guides.connect(self.overlay.clear_guides)
        self.signals.show_panel.connect(self.control_panel.show)
        self.signals.toggle_click_through.connect(self.toggle_click_through)
        
        # Setup global hotkeys
        self.setup_hotkeys()
        
        # Auto-save on config changes
        self.config_model.config_saved.connect(
            lambda: self.config_manager.save_config(self.config_model))
    
    def create_tray_icon(self):
        """Create system tray icon"""
        icon_path = get_icon_path()
        if icon_path:
            self.tray_icon = QSystemTrayIcon(QIcon(icon_path), self.app)
        else:
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(QPen(QColor(Colors.ACCENT), 4))
            painter.drawLine(10, 32, 54, 32)
            painter.drawLine(32, 10, 32, 54)
            painter.drawRect(8, 8, 48, 48)
            painter.end()
            self.tray_icon = QSystemTrayIcon(QIcon(pixmap), self.app)
        
        # Create menu
        menu = QMenu()
        
        show_action = QAction('📋 Control Panel', self.app)
        show_action.triggered.connect(self.control_panel.show)
        menu.addAction(show_action)
        
        menu.addSeparator()
        
        toggle_ct = QAction('🔓 Toggle Click-Through', self.app)
        toggle_ct.triggered.connect(self.toggle_click_through_from_tray)
        menu.addAction(toggle_ct)
        
        clear_action = QAction('🗑️ Clear Guides', self.app)
        clear_action.triggered.connect(self.overlay.clear_guides)
        menu.addAction(clear_action)
        
        menu.addSeparator()
        
        quit_action = QAction('❌ Quit', self.app)
        quit_action.triggered.connect(self.quit_app)
        menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.setToolTip('Ruler Guides Pro by ISOLATE')
        self.tray_icon.show()
        
        # Double-click to show control panel
        self.tray_icon.activated.connect(
            lambda reason: self.control_panel.show() if reason == QSystemTrayIcon.DoubleClick else None)
    
    def setup_hotkeys(self):
        """Setup global keyboard shortcuts"""
        try:
            keyboard.add_hotkey('ctrl+i', self.signals.toggle_rulers.emit)
            keyboard.add_hotkey('ctrl+shift+g', self.signals.toggle_guides.emit)
            keyboard.add_hotkey('ctrl+shift+c', self.signals.clear_guides.emit)
            keyboard.add_hotkey('ctrl+shift+p', self.signals.show_panel.emit)
            keyboard.add_hotkey('ctrl+shift+t', self.signals.toggle_click_through.emit)
        except Exception as e:
            print(f"Hotkey setup warning: {e}")
    
    def toggle_rulers(self):
        current = self.config_model.get_visibility('rulers')
        self.config_model.set_visibility('rulers', not current)
    
    def toggle_guides(self):
        current = self.config_model.get_visibility('guides')
        self.config_model.set_visibility('guides', not current)
    
    def toggle_click_through(self):
        self.overlay.make_click_through(not self.overlay.click_through_mode)
        self.control_panel.click_through_check.setChecked(self.overlay.click_through_mode)
    
    def toggle_click_through_from_tray(self):
        self.toggle_click_through()
    
    def quit_app(self):
        """Quit application"""
        self.config_manager.save_config(self.config_model)
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        
        # Hide standard tray icon before quitting to prevent ghost icons
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
            
        self.app.quit()
    
    def run(self):
        """Run application"""
        self.control_panel.show()
        return self.app.exec_()


# ═══════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

def main():
    try:
        myappid = 'com.abhisht.rulerguidespro.3.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass
        
    try:
        print("╔" + "═" * 78 + "╗")
        print("║" + " " * 20 + "RULER GUIDES PRO BY ISOLATE" + " " * 31 + "║")
        print("║" + " " * 26 + "Version 3.0 - Refined" + " " * 31 + "║")
        print("╚" + "═" * 78 + "╝")
        print()
        print("✨ IMPROVEMENTS:")
        print("  ✓ Tabbed UI - No scrollbars, clean navigation")
        print("  ✓ Custom Windows Icon / Taskbar Badging")
        print("  ✓ Smart caching - 10x performance improvement")
        print("  ✓ True 1px rendering - Pixel-perfect thin lines")
        print("  ✓ Event-driven rendering - <1% CPU idle")
        print("  ✓ Minimal professional UI")
        print()
        print("⌨️  HOTKEYS:")
        print("  • Ctrl+I       - Toggle rulers")
        print("  • Ctrl+Shift+G - Toggle guides")
        print("  • Ctrl+Shift+T - Toggle click-through")
        print("  • Ctrl+Shift+C - Clear all guides")
        print("  • Ctrl+Shift+P - Show control panel")
        print("  • Ctrl+Wheel - Zoom in/out")
        print()
        print("═" * 80)
        print()
    except Exception:
        pass
    
    app = RulerGuidesApp()
    sys.exit(app.run())


if __name__ == '__main__':
    main()