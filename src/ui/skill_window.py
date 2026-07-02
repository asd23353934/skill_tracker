"""
技能倒數視窗模組 — PySide6 版本
無邊框透明浮動視窗，QPainter 繪製 RPG 金色邊框 + 倒數文字 + 灰色矩形遮罩
取代原版 tkinter.Toplevel + Canvas 方案
"""

import time
import math

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QRect, QRectF
from PySide6.QtGui import (
    QPainter, QPen, QColor, QFont, QFontMetrics, QPixmap, QImage, QBrush,
)

from src.ui.theme import AppTheme
from src.ui.window_geometry import clamp_to_screen
from src.ui_v2.theme_v2 import V2Theme
from src.ui_v2.lucide import lucide_pixmap


class SkillWindow(QWidget):
    """技能/怪物倒數浮動視窗 — QPainter 繪製（V2 配色 + 圓角）"""

    # V2 調性常量（顏色／字型家族，不含任何尺寸）
    COLOR_BORDER       = V2Theme.ORANGE         # 外層邊框：V2 主 CTA
    COLOR_BORDER_INNER = V2Theme.BORDER_HOVER   # 內層邊框：低調灰紫
    COLOR_TEXT         = V2Theme.TEXT_HI        # 倒數文字：亮白
    COLOR_OUTLINE      = V2Theme.BG_BOTTOM      # 文字描邊：深黑
    COLOR_CLOSE        = V2Theme.TEXT_HI        # 關閉鈕常態 X（亮白更顯眼）
    COLOR_CLOSE_BG     = V2Theme.BG_ELEVATED    # 關閉鈕常態底色（半透明灰）
    COLOR_CLOSE_HOVER  = V2Theme.TEXT_HI        # 關閉鈕 hover X
    COLOR_CLOSE_HOVER_BG = V2Theme.ORANGE       # 關閉鈕 hover 底色
    COLOR_FLASH        = V2Theme.YELLOW         # 提前提示閃爍
    COLOR_HOTKEY       = V2Theme.ORANGE         # 圖片下方按鍵字幕（橘色＝可按的鍵）
    COLOR_HOTKEY_BG    = V2Theme.BG_ELEVATED    # 按鍵字幕底：深黑灰、不透明
    FONT_FAMILY        = V2Theme.FONT_FAMILY    # 統一字型家族

    # 按鍵字幕與圖片之間的間距（像素）
    HOTKEY_GAP = 3
    # 按鍵字幕底圓角（小圓角＝方正而非膠囊）
    HOTKEY_BG_RADIUS = 3

    # 邊框寬度（嚴禁調整 — 影響整體尺寸計算）
    BORDER_W       = 2
    INNER_BORDER_W = 1

    def __init__(
        self, skill, player, position, skill_image, on_close,
        enable_sound, skill_id,
        is_permanent   = False,
        is_loop        = False,
        start_at_zero  = False,
        window_alpha   = None,
        alert_enabled  = False,
        alert_before_seconds = 0,
        on_alert       = None,
        on_drag_start  = None,
        on_drag_motion = None,
        on_drag_end    = None,
        window_size    = 64,
        skill_image_path = None,
        sound_manager  = None,
        sound_filename = "",
        alert_sound_filename = "",
        count_up       = False,
        title          = None,
        idle_start     = False,
        enable_end_sound   = None,
        enable_alert_sound = None,
    ):
        """初始化倒數視窗

        Args:
            skill:               技能/怪物資料字典
            player:              玩家名稱
            position:            (x, y) 視窗位置
            skill_image:         預留（舊版 PhotoImage，Qt 版本不使用）
            on_close:            視窗關閉回調 callback(window)
            enable_sound:        是否啟用音效
            skill_id:            技能/怪物 ID
            is_permanent:        是否常駐
            is_loop:             是否循環
            start_at_zero:       是否從 0 開始（常駐技能）
            window_alpha:        視窗透明度
            alert_enabled:       是否啟用提前提示
            alert_before_seconds: 提前幾秒提示
            on_alert:            提示回調
            on_drag_start:       拖曳開始回調 (global_x, global_y)
            on_drag_motion:      拖曳中回調 (global_x, global_y)
            on_drag_end:         拖曳結束回調 (global_x, global_y)
            window_size:         視窗寬高（像素）
            skill_image_path:    技能圖片路徑
            sound_manager:       音效管理器
            sound_filename:      完成音效
            alert_sound_filename: 提示音效
            count_up:            是否正數模式（怪物）
            title:               標題文字（可選）
            idle_start:          是否以 idle 狀態啟動（常駐怪物）
        """
        # 無邊框透明置頂工具視窗
        super().__init__(
            None,
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setMouseTracking(True)

        # 參數儲存
        self.skill               = skill
        self.player              = player
        self.on_close            = on_close
        self.enable_sound        = enable_sound
        # 完成音 / 提前音各自開關；未指定時沿用 enable_sound（相容舊呼叫端）
        self.enable_end_sound    = enable_sound if enable_end_sound is None else enable_end_sound
        self.enable_alert_sound  = enable_sound if enable_alert_sound is None else enable_alert_sound
        self.skill_id            = skill_id
        self.is_permanent        = is_permanent
        self.is_loop             = is_loop
        self.skill_image         = skill_image      # 保留相容性，Qt 版本不使用
        self._skill_image_path   = skill_image_path
        self.count_up            = count_up
        self.title               = title
        self.idle_start          = idle_start
        # 圖片下方要顯示的按鍵（skill / monster dict 內的 hotkey）；空字串不顯示
        self._hotkey             = str((skill or {}).get("hotkey") or "").strip()

        self.window_alpha        = window_alpha if window_alpha is not None else 0.95
        self.window_size         = window_size

        self.alert_enabled       = alert_enabled
        self.alert_before_seconds = alert_before_seconds
        self.on_alert            = on_alert
        self.alert_triggered     = False

        self.sound_manager       = sound_manager
        self.sound_filename      = sound_filename
        self.alert_sound_filename = alert_sound_filename

        self.on_drag_start       = on_drag_start
        self.on_drag_motion      = on_drag_motion
        self.on_drag_end         = on_drag_end

        self.total     = skill.get("cooldown") or skill.get("respawn_time", 0)
        self.remaining = 0 if (start_at_zero or count_up) else self.total

        self.running    = False
        self.start_time = None
        self.end_time   = None

        # 圖片遮罩快取
        self._base_pil_image      = None
        self._overlay_pixmap: QPixmap | None = None
        self._last_overlay_degree = -1

        # 閃爍狀態
        self._flash_active = False
        self._flash_count  = 0

        # 關閉按鈕 hover
        self._close_hovered = False

        # 防止重複關閉
        self._closed = False

        # 當前顯示文字
        self._current_display_text = "0" if count_up else self._fmt_seconds(self.remaining)

        # 計算視窗尺寸
        self._calc_dimensions()

        # 載入圖片
        self._setup_image()

        # 套用透明度並顯示（播放 0 → window_alpha 淡入動畫）
        self.setWindowOpacity(0.0)
        self.resize(self._canvas_width, self._total_height)
        cx, cy = clamp_to_screen(
            position[0], position[1], self._canvas_width, self._total_height
        )
        self.move(cx, cy)
        self.show()

        self._enter_anim = AppTheme.make_anim(
            self, b"windowOpacity", 0.0, self.window_alpha, duration=180)
        self._enter_anim.start()

        # 計時 Timer（tick 週期 100ms，快秒切換 50ms）
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._tick)

        # 閃爍 Timer
        self._flash_timer = QTimer(self)
        self._flash_timer.setInterval(120)
        self._flash_timer.timeout.connect(self._flash_tick)

        # 啟動邏輯
        if count_up:
            if not idle_start:
                self.start_countdown()
            else:
                self._update_overlay(0)
                self.update()
        elif not start_at_zero:
            self.start_countdown()
        else:
            self._update_overlay(0)
            self.update()

    # --------------------------------------------------
    # 尺寸計算
    # --------------------------------------------------

    def _calc_dimensions(self):
        """計算視窗各區塊高度與關閉按鈕位置"""
        ws = self.window_size
        bw = self.BORDER_W

        self._canvas_width = ws + bw * 2

        if self.count_up:
            # 怪物正數：時間文字在上，留更多空間避免裁切
            self._text_height  = int(ws * 0.5)
            self._title_height = 0
        else:
            self._title_height = max(18, int(ws * 0.28)) if self.title else 0
            self._text_height  = int(ws * 0.5)  # 與怪物視窗一致，確保圖片區域對齊

        self._img_y0     = self._text_height + self._title_height
        self._img_y1     = self._img_y0 + ws + bw * 2
        self._text_y     = self._text_height // 2    # 文字垂直中心

        # 圖片下方按鍵字幕區（有 hotkey 才佔高度；字級會自動縮放避免跑版）
        # 與圖片之間留一點間距，字幕底再鋪深黑灰不透明方正底
        gap = self.HOTKEY_GAP if self._hotkey else 0
        self._hotkey_height = max(12, int(ws * 0.24)) if self._hotkey else 0
        self._hotkey_y0     = self._img_y1 + gap
        self._total_height  = self._hotkey_y0 + self._hotkey_height

        # 關閉按鈕矩形（圖片區域右上角）
        close_size = 16
        pad        = 2
        self._close_rect = QRect(
            self._canvas_width - close_size - pad - bw,
            self._img_y0 + pad + bw,
            close_size,
            close_size,
        )

    # --------------------------------------------------
    # 圖片載入與遮罩
    # --------------------------------------------------

    def _setup_image(self):
        """載入技能圖片並建立初始 QPixmap 快取"""
        from PIL import Image

        ws = self.window_size
        if self._skill_image_path:
            try:
                img = Image.open(self._skill_image_path).convert("RGBA")
                img = img.resize((ws, ws), Image.Resampling.LANCZOS)
                self._base_pil_image = img
            except Exception:
                self._base_pil_image = Image.new("RGBA", (ws, ws), (128, 128, 128, 255))
        else:
            self._base_pil_image = Image.new("RGBA", (ws, ws), (128, 128, 128, 255))

        self._overlay_pixmap = self._pil_to_qpixmap(self._base_pil_image)

    @staticmethod
    def _pil_to_qpixmap(pil_img) -> QPixmap:
        """PIL RGBA Image → QPixmap

        Args:
            pil_img: PIL Image（必須為 RGBA 模式）

        Returns:
            QPixmap 物件
        """
        data  = pil_img.tobytes("raw", "RGBA")
        qimg  = QImage(data, pil_img.width, pil_img.height,
                       QImage.Format.Format_RGBA8888)
        return QPixmap.fromImage(qimg)

    def _create_overlay_pixmap(self, progress: float) -> QPixmap:
        """建立帶有灰色矩形遮罩的技能圖片 QPixmap

        遮罩從底部向上填滿。progress=0 無遮罩，progress=1 全部遮蔽。

        Args:
            progress: 0.0 ~ 1.0

        Returns:
            QPixmap
        """
        from PIL import Image, ImageDraw

        if self._base_pil_image is None:
            return QPixmap()

        base = self._base_pil_image.copy()
        if progress <= 0:
            return self._pil_to_qpixmap(base)

        overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
        draw    = ImageDraw.Draw(overlay)
        w, h    = base.size
        fill_h  = int(min(progress, 1.0) * h)
        if fill_h > 0:
            draw.rectangle([0, h - fill_h, w, h], fill=AppTheme.OVERLAY_COLOR)

        result = Image.alpha_composite(base, overlay)
        return self._pil_to_qpixmap(result)

    def _update_overlay(self, progress: float):
        """更新遮罩圖片快取（僅像素高度變化時重新合成）

        Args:
            progress: 0.0 ~ 1.0
        """
        pixel_h = int(progress * self.window_size)
        if pixel_h == self._last_overlay_degree:
            return
        self._last_overlay_degree = pixel_h
        new_pixmap = self._create_overlay_pixmap(progress)
        if not new_pixmap.isNull():
            self._overlay_pixmap = new_pixmap
        self.update()   # 觸發 paintEvent

    # --------------------------------------------------
    # 繪製（QPainter）
    # --------------------------------------------------

    def paintEvent(self, event):  # noqa: N802
        """繪製全部視覺元素：文字 + 圖片 + 金色邊框 + 關閉按鈕"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        ws  = self.window_size
        bw  = self.BORDER_W
        cw  = self._canvas_width
        iy0 = self._img_y0
        iy1 = self._img_y1

        # ===== 計時文字（倒數 / 正數）=====
        self._paint_timer_text(painter, cw)

        # ===== 標題文字（僅 countdown 模式且有設定 title）=====
        if self.title and not self.count_up:
            self._paint_title_text(painter, cw)

        # ===== 技能圖片（含遮罩）=====
        if self._overlay_pixmap and not self._overlay_pixmap.isNull():
            painter.drawPixmap(bw, iy0 + bw, self._overlay_pixmap)

        # ===== 外層邊框（V2 ORANGE / alert 時 YELLOW，圓角）=====
        border_color = self.COLOR_FLASH if self._flash_active else self.COLOR_BORDER
        pen = QPen(QColor(border_color), bw)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        outer_rect = QRectF(bw / 2, iy0 + bw / 2,
                            cw - bw, iy1 - iy0 - bw)
        painter.drawRoundedRect(outer_rect, V2Theme.R_SM, V2Theme.R_SM)

        # ===== 內層細邊框（低調灰紫，圓角同心）=====
        ibw = self.INNER_BORDER_W
        inner_pen = QPen(QColor(self.COLOR_BORDER_INNER), ibw)
        inner_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(inner_pen)
        ib = bw + ibw / 2
        inner_rect = QRectF(ib, iy0 + ib, cw - ib * 2, iy1 - iy0 - ib * 2)
        # 內框半徑比外框小 1px，保持同心弧度觀感
        painter.drawRoundedRect(inner_rect, V2Theme.R_SM - 1, V2Theme.R_SM - 1)

        # ===== 關閉按鈕 =====
        self._paint_close_btn(painter)

        # ===== 按鍵字幕（圖片下方，字級自動縮放避免跑版）=====
        if self._hotkey:
            self._paint_hotkey_text(painter, cw)

        painter.end()

    def _paint_timer_text(self, painter: QPainter, cw: int):
        """繪製計時文字（附描邊）"""
        text      = self._current_display_text
        font_size = max(18, int(self.window_size * 0.4))
        font      = QFont(self.FONT_FAMILY, font_size)
        font.setBold(True)
        painter.setFont(font)

        text_rect = QRect(0, 0, cw, self._text_height)
        flags     = Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter

        # 描邊（8 方向偏移）
        offset = 2
        painter.setPen(QColor(self.COLOR_OUTLINE))
        for dx in (-offset, 0, offset):
            for dy in (-offset, 0, offset):
                if dx == 0 and dy == 0:
                    continue
                painter.drawText(text_rect.translated(dx, dy), flags, text)

        # 主文字
        painter.setPen(QColor(self.COLOR_TEXT))
        painter.drawText(text_rect, flags, text)

    def _paint_title_text(self, painter: QPainter, cw: int):
        """繪製技能標題（緊貼圖片上方）"""
        title_font_size = max(9, int(self.window_size * 0.17))
        font            = QFont(self.FONT_FAMILY, title_font_size)
        font.setBold(True)
        painter.setFont(font)

        title_rect = QRect(0,
                           self._text_height,
                           cw,
                           self._title_height)
        flags = Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter

        # 描邊
        painter.setPen(QColor(self.COLOR_OUTLINE))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                painter.drawText(title_rect.translated(dx, dy), flags, self.title)

        # 主文字
        painter.setPen(QColor(self.COLOR_TEXT))
        painter.drawText(title_rect, flags, self.title)

    def _fit_hotkey_font(self, text: str, max_w: int, base_size: int,
                         min_size: int = 6):
        """挑出能塞進 max_w 的最大字級（粗體）；到最小字級仍超寬則 elide

        固定窗寬下避免按鍵文字撐破版面：由 base_size 往下找第一個寬度 ≤ max_w
        的字級，最小到 min_size；min_size 仍不夠寬就以 ellipsis 截斷。

        Returns:
            (QFont, 實際要畫的文字)
        """
        size = max(min_size, base_size)
        while size > min_size:
            font = QFont(self.FONT_FAMILY, size)
            font.setBold(True)
            if QFontMetrics(font).horizontalAdvance(text) <= max_w:
                return font, text
            size -= 1
        font = QFont(self.FONT_FAMILY, min_size)
        font.setBold(True)
        elided = QFontMetrics(font).elidedText(
            text, Qt.TextElideMode.ElideRight, max_w)
        return font, elided

    def _paint_hotkey_text(self, painter: QPainter, cw: int):
        """繪製圖片下方的按鍵字幕（橘色 + 描邊，字級自動縮放）"""
        pad   = 3
        max_w = max(1, cw - pad * 2)
        base  = max(8, int(self.window_size * 0.22))
        font, text = self._fit_hotkey_font(self._hotkey, max_w, base)
        painter.setFont(font)

        # 淡灰不透明底（寬度與小窗一致，高度即字幕區＝比文字略高，方正小圓角）
        bg_rect = QRectF(0, self._hotkey_y0, cw, self._hotkey_height)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(self.COLOR_HOTKEY_BG)))
        painter.drawRoundedRect(bg_rect, self.HOTKEY_BG_RADIUS, self.HOTKEY_BG_RADIUS)

        rect  = QRect(pad, self._hotkey_y0, cw - pad * 2, self._hotkey_height)
        flags = Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter

        # 描邊（提高深色 / 亮色背景上的可讀性）
        painter.setPen(QColor(self.COLOR_OUTLINE))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                painter.drawText(rect.translated(dx, dy), flags, text)

        # 主文字
        painter.setPen(QColor(self.COLOR_HOTKEY))
        painter.drawText(rect, flags, text)

    def _paint_close_btn(self, painter: QPainter):
        """繪製關閉按鈕 — V2 風格：常態 dim X、hover 時 ORANGE 圓角填色 + 亮 X"""
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # 底色：常態深灰、hover ORANGE；都帶圓角
        bg_rect = QRectF(self._close_rect)
        if self._close_hovered:
            bg_color = QColor(self.COLOR_CLOSE_HOVER_BG)
            x_color  = QColor(self.COLOR_CLOSE_HOVER)
        else:
            bg_color = QColor(self.COLOR_CLOSE_BG)
            bg_color.setAlpha(220)   # 常態略透，避免過搶
            x_color  = QColor(self.COLOR_CLOSE)

        # 細 ORANGE 框線讓按鈕邊緣可見
        painter.setPen(QPen(QColor(V2Theme.ORANGE), 1))
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(bg_rect, V2Theme.R_SM, V2Theme.R_SM)

        # 用 lucide "x" SVG 繪製關閉符號（與 V2 header 同一套 icon）
        cr       = self._close_rect
        icon_sz  = 10                                          # 在 16×16 按鈕內留 3px padding
        pix      = lucide_pixmap("x", x_color.name(), icon_sz, stroke=1.8)
        px       = cr.x() + (cr.width()  - icon_sz) // 2
        py       = cr.y() + (cr.height() - icon_sz) // 2
        painter.drawPixmap(px, py, pix)
        painter.restore()

    # --------------------------------------------------
    # 閃爍邊框
    # --------------------------------------------------

    def _flash_tick(self):
        """閃爍計時 tick（亮金 ↔ 原金切換）"""
        if self._flash_count >= 6:
            self._flash_active = False
            self._flash_count  = 0
            self._flash_timer.stop()
            self.update()
            return
        self._flash_active = (self._flash_count % 2 == 0)
        self._flash_count += 1
        self.update()

    # --------------------------------------------------
    # 滑鼠事件（拖曳 + 關閉按鈕）
    # --------------------------------------------------

    def mousePressEvent(self, event):  # noqa: N802
        """左鍵點擊：關閉按鈕判斷或開始拖曳"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self._close_rect.contains(event.position().toPoint()):
                self.close()
            else:
                gp = event.globalPosition().toPoint()
                if self.on_drag_start:
                    self.on_drag_start(gp.x(), gp.y())

    def mouseMoveEvent(self, event):  # noqa: N802
        """滑鼠移動：更新 hover 狀態並通知拖曳"""
        pos         = event.position().toPoint()
        new_hovered = self._close_rect.contains(pos)
        if new_hovered != self._close_hovered:
            self._close_hovered = new_hovered
            self.update()

        gp = event.globalPosition().toPoint()
        if self.on_drag_motion:
            self.on_drag_motion(gp.x(), gp.y())

    def mouseReleaseEvent(self, event):  # noqa: N802
        """左鍵釋放：結束拖曳"""
        if event.button() == Qt.MouseButton.LeftButton:
            gp = event.globalPosition().toPoint()
            if self.on_drag_end:
                self.on_drag_end(gp.x(), gp.y())

    # --------------------------------------------------
    # 倒數邏輯
    # --------------------------------------------------

    def start_countdown(self):
        """開始倒數/正數計時"""
        self.stop_countdown()
        self.running        = True
        self.alert_triggered = False
        self.start_time     = time.perf_counter()
        self.end_time       = self.start_time + self.total

        self._update_display()
        self._update_overlay(0)
        self._timer.start(100)

    def stop_countdown(self):
        """停止計時"""
        self.running = False
        if self._timer.isActive():
            self._timer.stop()

    def reset_countdown(self):
        """重置並重新開始"""
        self.remaining       = self.total
        self.alert_triggered = False
        self._last_overlay_degree = -1
        self._update_display()
        self.start_countdown()

    def restart_countdown(self):
        """重新開始計時（供 WindowManager 呼叫）"""
        self.reset_countdown()

    def _tick(self):
        """計時 tick — 由 QTimer 觸發"""
        if not self.running:
            return

        current_time = time.perf_counter()
        elapsed      = current_time - self.start_time

        if self.count_up:
            self._tick_count_up(elapsed)
        else:
            self._tick_count_down(elapsed)

    def _tick_count_up(self, elapsed: float):
        """正數模式 tick — 從 0 數到目標時間"""
        elapsed_sec = int(elapsed)
        progress    = min(1.0, elapsed / self.total) if self.total > 0 else 1.0
        self._update_overlay(progress)

        # 提前提示
        remaining_to_target = self.total - elapsed_sec
        if (self.alert_enabled and not self.alert_triggered
                and self.alert_before_seconds > 0
                and 0 < remaining_to_target <= self.alert_before_seconds):
            self._trigger_alert()

        if elapsed >= self.total:
            self.remaining = self.total
            self._update_display_text(self._fmt_seconds(self.total))
            self._update_overlay(1.0)
            self._on_finish()
        else:
            if elapsed_sec != self.remaining:
                self.remaining = elapsed_sec
                self._update_display_text(self._fmt_seconds(self.remaining))
            self._timer.start(100)

    def _tick_count_down(self, elapsed: float):
        """倒數模式 tick — 從目標時間數到 0"""
        raw_remaining = self.total - elapsed
        progress      = min(1.0, elapsed / self.total) if self.total > 0 else 1.0
        self._update_overlay(progress)

        if 0 < raw_remaining < 1.0:
            # 快秒顯示（顯示小數）
            self._update_display_text(f"{raw_remaining:.1f}")

            new_remaining = max(0, math.ceil(raw_remaining))
            if new_remaining != self.remaining:
                self.remaining = new_remaining
                self._check_alert()

            self._timer.start(50)   # 快秒使用更短間隔

        elif raw_remaining <= 0:
            self.remaining = 0
            self._update_display_text("0")
            self._update_overlay(1.0)
            self._on_finish()

        else:
            new_remaining = max(0, math.ceil(raw_remaining))
            if new_remaining != self.remaining:
                self.remaining = new_remaining
                self._update_display()
                self._check_alert()
            self._timer.start(100)

    def _check_alert(self):
        """檢查是否需要觸發提前提示"""
        if (self.alert_enabled
                and not self.alert_triggered
                and self.alert_before_seconds > 0
                and self.remaining <= self.alert_before_seconds):
            self._trigger_alert()

    def _on_finish(self):
        """計時結束處理"""
        # 若設定 0 秒提示，在結束時觸發
        if self.alert_enabled and not self.alert_triggered and self.alert_before_seconds == 0:
            self._trigger_alert()

        if self.enable_end_sound:
            self._play_sound()

        if self.is_loop:
            self.running = False
            self._loop_restart()

        elif self.is_permanent and self.count_up:
            # 常駐怪物：時間到後重置為 idle（等待下次按鍵）
            self.running  = False
            self.remaining = 0
            self._last_overlay_degree = -1
            self._update_overlay(0)
            self._update_display_text("0")

        elif self.count_up:
            # 非常駐怪物：停留畫面（遮罩全滿，不自動關閉）
            self.running = False

        elif not self.is_permanent:
            # 一般技能：2 秒後關閉
            QTimer.singleShot(2000, self.close)

        else:
            # 常駐技能：重置遮罩回待機狀態
            self._update_display()
            self._last_overlay_degree = -1
            self._update_overlay(0)

    def _loop_restart(self):
        """循環模式：重新開始

        排程錨定：start_time 接續「上一輪的理論結束點」(end_time)，吸收每輪的
        偵測延遲，避免誤差逐輪累積成秒差（長時間循環不漂移）。若落後超過一個
        完整週期（休眠 / 卡頓 / debugger 暫停），重新對齊到當下，避免一次爆衝補進度。
        """
        now = time.perf_counter()
        self.start_time      = self.end_time
        if now - self.start_time > self.total:
            self.start_time  = now
        self.end_time        = self.start_time + self.total
        self.remaining       = 0 if self.count_up else self.total
        self.alert_triggered = False
        self._last_overlay_degree = -1

        self._update_display()
        self._update_overlay(0)

        self.running = True
        self._tick()

    # --------------------------------------------------
    # 提前提示
    # --------------------------------------------------

    def _trigger_alert(self):
        """觸發提前提示：閃爍邊框 + 音效"""
        self.alert_triggered = True

        # 開始邊框閃爍
        self._flash_count  = 0
        self._flash_active = True
        self._flash_timer.start()
        self.update()

        if self.enable_alert_sound and self.sound_manager and self.alert_sound_filename:
            self.sound_manager.play_alert(self.alert_sound_filename)

        if self.on_alert:
            self.on_alert(self.skill["name"])

    # --------------------------------------------------
    # 顯示輔助
    # --------------------------------------------------

    def _update_display(self):
        """根據 self.remaining 更新顯示文字"""
        text = "0" if self.remaining <= 0 else self._fmt_seconds(self.remaining)
        self._update_display_text(text)

    @staticmethod
    def _fmt_seconds(seconds: int) -> str:
        """>600 秒切換為分鐘顯示（ceil），避免長 buff 倒數時整排數字塞滿小窗

        嚴格大於 600 才轉分鐘（剛好 600 秒仍以「600」顯示）；切換瞬間是
        「11m」→「600」這種跳變，刻意維持，避免「10m」→「600」更突兀。

        Args:
            seconds: 剩餘秒數整數

        Returns:
            ≤600 → 純秒數字串（例如 "599"）；>600 → 分鐘字串（例如 "11m"）
        """
        if seconds > 600:
            return f"{math.ceil(seconds / 60)}m"
        return str(seconds)

    def _update_display_text(self, text: str):
        """更新顯示文字並觸發重繪

        Args:
            text: 要顯示的文字
        """
        if self._current_display_text != text:
            self._current_display_text = text
            self.update()

    def _play_sound(self):
        """播放完成音效"""
        if self.sound_manager and self.sound_filename:
            self.sound_manager.play(self.sound_filename)

    # --------------------------------------------------
    # 外部 API
    # --------------------------------------------------

    def update_position(self, x: int, y: int):
        """更新視窗位置（供 WindowManager.reposition_all 呼叫）

        Args:
            x: 螢幕 X 座標
            y: 螢幕 Y 座標
        """
        try:
            self.move(x, y)
        except Exception:
            pass

    # --------------------------------------------------
    # 視窗關閉
    # --------------------------------------------------

    def close(self):
        """關閉視窗（停止計時 → 通知 WindowManager → 銷毀）"""
        if self._closed:
            return
        self._closed = True

        self.stop_countdown()
        if hasattr(self, "_flash_timer") and self._flash_timer.isActive():
            self._flash_timer.stop()

        try:
            self.on_close(self)
        except Exception:
            pass

        super().close()
