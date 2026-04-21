"""
覆蓋圖片浮動視窗模組 — PySide6 版本
無邊框透明浮動視窗，顯示靜態圖片或動畫 GIF
hover 才顯示 X 關閉按鈕；支援拖曳移動、透明度調整
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QRect, QPoint
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPixmap, QImage
from PIL import Image, ImageSequence


class OverlayWindow(QWidget):
    """覆蓋圖片浮動視窗 — 支援 PNG / JPG / GIF（含動畫）

    全透明背景，hover 才顯示 X 關閉按鈕。
    """

    _CLOSE_R      = 10  # 關閉按鈕圓形半徑（px）
    _RESIZE_STEP  = 10  # 方向鍵縮放步長（px）
    _HANDLE_SIZE  = 20  # 右下角滑鼠縮放區塊大小（px）

    def __init__(
        self,
        overlay_id: str,
        image_path: str,
        alpha: float,
        position: tuple,
        on_close,
        on_position_change,
        on_size_change=None,
        width: int = None,
        height: int = None,
    ):
        """初始化覆蓋圖視窗

        Args:
            overlay_id:          覆蓋圖唯一 ID
            image_path:          圖片絕對路徑
            alpha:               視窗透明度 0.1–1.0
            position:            (x, y) 螢幕座標
            on_close:            callback(overlay_id)
            on_position_change:  callback(overlay_id, x, y) 拖曳結束時呼叫
            on_size_change:      callback(overlay_id, w, h) 方向鍵調整尺寸後呼叫
            width:               指定顯示寬度（None 則自動）
            height:              指定顯示高度（None 則自動）
        """
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setMouseTracking(True)

        self.overlay_id          = overlay_id
        self.on_close            = on_close
        self.on_position_change  = on_position_change
        self.on_size_change      = on_size_change

        # 動畫狀態
        self._frames:     list[QPixmap] = []
        self._pil_frames: list          = []   # 原始 PIL 幀（RGBA）供重新縮放使用
        self._delays:     list[int]     = []
        self._frame_idx                 = 0

        # 拖曳暫存
        self._drag_offset    = QPoint()
        self._pressing_close = False

        # 滑鼠縮放暫存
        self._resizing        = False
        self._resize_start_pos  = QPoint()
        self._resize_start_size = (0, 0)

        # UI 狀態
        self._close_visible = False
        self._closed        = False

        # 載入圖片 → 設定 img_w / img_h
        self._load_image(image_path, width, height)

        # 關閉按鈕矩形（右上角）
        r = self._CLOSE_R
        self._close_rect = QRect(self.img_w - r * 2 - 4, 4, r * 2, r * 2)

        # 動畫計時器
        self._anim_timer = QTimer(self)
        self._anim_timer.setSingleShot(True)
        self._anim_timer.timeout.connect(self._animate)

        # 接受鍵盤焦點（方向鍵調整大小）
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        # 顯示
        self.setWindowOpacity(max(0.1, min(1.0, alpha)))
        self.resize(self.img_w, self.img_h)
        self.move(position[0], position[1])
        self.show()

        # 啟動 GIF 動畫
        if len(self._frames) > 1:
            self._anim_timer.start(self._delays[0])

    # --------------------------------------------------
    # 圖片載入
    # --------------------------------------------------

    def _load_image(self, path: str, target_w: int = None, target_h: int = None):
        """載入圖片（靜態或 GIF 動畫）並預先轉為 QPixmap 列表

        Args:
            path:     圖片路徑
            target_w: 目標寬度（None 則自動縮放，最長邊不超過 600px）
            target_h: 目標高度（None 則自動縮放）
        """
        with Image.open(path) as src:
            is_gif = src.format == "GIF"
            ow, oh = src.size

            # 計算顯示尺寸
            if target_w and target_h:
                self.img_w = max(1, target_w)
                self.img_h = max(1, target_h)
            else:
                max_dim = 600
                scale   = min(1.0, max_dim / max(ow, oh))
                self.img_w = max(1, int(ow * scale))
                self.img_h = max(1, int(oh * scale))

            if is_gif:
                raw_frames = []
                for frame in ImageSequence.Iterator(src):
                    raw_frames.append(frame.copy())
                    self._delays.append(max(frame.info.get("duration", 100), 30))
                self._pil_frames = [f.convert("RGBA") for f in raw_frames]
            else:
                self._pil_frames = [src.convert("RGBA")]
                self._delays.append(0)

        self._render_frames_at_size(self.img_w, self.img_h)

    @staticmethod
    def _pil_to_qpixmap(pil_img) -> QPixmap:
        """PIL RGBA Image → QPixmap"""
        data  = pil_img.tobytes("raw", "RGBA")
        qimg  = QImage(data, pil_img.width, pil_img.height,
                       QImage.Format.Format_RGBA8888)
        return QPixmap.fromImage(qimg)

    def _render_frames_at_size(self, w: int, h: int):
        """將 _pil_frames 以指定尺寸重新轉換為 QPixmap 列表

        Args:
            w: 目標寬度
            h: 目標高度
        """
        size = (max(1, w), max(1, h))
        self._frames = [
            self._pil_to_qpixmap(f.resize(size, Image.Resampling.LANCZOS))
            for f in self._pil_frames
        ]

    # --------------------------------------------------
    # 動畫
    # --------------------------------------------------

    def _animate(self):
        """GIF 動畫 tick"""
        if len(self._frames) <= 1:
            return
        self._frame_idx = (self._frame_idx + 1) % len(self._frames)
        self.update()
        self._anim_timer.start(self._delays[self._frame_idx])

    # --------------------------------------------------
    # 繪製
    # --------------------------------------------------

    def paintEvent(self, event):  # noqa: N802
        """繪製圖片 + 關閉按鈕 + 右下角縮放把手（hover 才顯示）"""
        if not self._frames:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 繪製當前幀
        painter.drawPixmap(0, 0, self._frames[self._frame_idx])

        if self._close_visible:
            # 關閉按鈕
            r = self._CLOSE_R
            painter.setBrush(QBrush(QColor("#cc2222")))
            painter.setPen(QPen(QColor("#ff5555"), 1))
            painter.drawEllipse(self._close_rect)
            close_font = QFont("Arial", 9)
            close_font.setBold(True)
            painter.setFont(close_font)
            painter.setPen(QColor("white"))
            painter.drawText(self._close_rect, Qt.AlignmentFlag.AlignCenter, "✕")

            # 右下角縮放把手（三角形）
            hs = self._HANDLE_SIZE
            x0, y0 = self.img_w - hs, self.img_h - hs
            painter.setBrush(QBrush(QColor(200, 200, 200, 160)))
            painter.setPen(Qt.PenStyle.NoPen)
            from PySide6.QtGui import QPolygon
            triangle = QPolygon([
                QPoint(self.img_w,      self.img_h - hs),
                QPoint(self.img_w,      self.img_h),
                QPoint(self.img_w - hs, self.img_h),
            ])
            painter.drawPolygon(triangle)

        painter.end()

    # --------------------------------------------------
    # 滑鼠事件
    # --------------------------------------------------

    def _in_resize_handle(self, pos: QPoint) -> bool:
        """判斷座標是否在右下角縮放把手內

        Args:
            pos: 本地座標

        Returns:
            True 表示在縮放區域
        """
        hs = self._HANDLE_SIZE
        return pos.x() >= self.img_w - hs and pos.y() >= self.img_h - hs

    def enterEvent(self, event):  # noqa: N802
        """滑鼠進入：顯示關閉按鈕與縮放把手"""
        self._close_visible = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):  # noqa: N802
        """滑鼠離開：隱藏關閉按鈕與縮放把手"""
        self._close_visible = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):  # noqa: N802
        """左鍵按下：判斷關閉/縮放/拖曳"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            self.setFocus()
            if self._close_rect.contains(pos):
                self._pressing_close = True
                self._resizing       = False
            elif self._in_resize_handle(pos):
                self._resizing          = True
                self._pressing_close    = False
                self._resize_start_pos  = event.globalPosition().toPoint()
                self._resize_start_size = (self.img_w, self.img_h)
            else:
                self._pressing_close = False
                self._resizing       = False
                self._drag_offset    = pos

    def mouseMoveEvent(self, event):  # noqa: N802
        """滑鼠移動：縮放 or 拖曳；更新游標"""
        pos = event.pos()

        # 更新游標形狀
        if self._in_resize_handle(pos) and not self._pressing_close:
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return

        if self._resizing:
            delta = event.globalPosition().toPoint() - self._resize_start_pos
            new_w = max(20, self._resize_start_size[0] + delta.x())
            new_h = max(20, self._resize_start_size[1] + delta.y())
            self._apply_resize(new_w, new_h)
        elif not self._pressing_close:
            new_pos = event.globalPosition().toPoint() - self._drag_offset
            self.move(new_pos)

    def mouseReleaseEvent(self, event):  # noqa: N802
        """左鍵釋放：關閉 / 結束縮放 / 儲存位置"""
        if event.button() != Qt.MouseButton.LeftButton:
            return

        if self._pressing_close:
            pos = event.pos()
            if self._close_rect.contains(pos):
                self.close()
            self._pressing_close = False
            return

        if self._resizing:
            self._resizing = False
            if self.on_size_change:
                try:
                    self.on_size_change(self.overlay_id, self.img_w, self.img_h)
                except Exception:
                    pass
            return

        # 儲存新位置
        if self.on_position_change:
            try:
                p = self.pos()
                self.on_position_change(self.overlay_id, p.x(), p.y())
            except Exception:
                pass

    def _apply_resize(self, new_w: int, new_h: int):
        """套用新的尺寸（更新幀 + 視窗大小）

        Args:
            new_w: 新寬度
            new_h: 新高度
        """
        if new_w == self.img_w and new_h == self.img_h:
            return
        self.img_w = new_w
        self.img_h = new_h
        self._render_frames_at_size(new_w, new_h)
        r = self._CLOSE_R
        self._close_rect = QRect(self.img_w - r * 2 - 4, 4, r * 2, r * 2)
        self.resize(new_w, new_h)
        self.update()

    def keyPressEvent(self, event):  # noqa: N802
        """方向鍵調整圖片大小（↔ 寬度 / ↕ 高度，每次 10px）"""
        key  = event.key()
        step = self._RESIZE_STEP
        if key == Qt.Key.Key_Right:
            self._resize_by(step, 0)
        elif key == Qt.Key.Key_Left:
            self._resize_by(-step, 0)
        elif key == Qt.Key.Key_Down:
            self._resize_by(0, step)
        elif key == Qt.Key.Key_Up:
            self._resize_by(0, -step)
        else:
            super().keyPressEvent(event)

    def _resize_by(self, dw: int, dh: int):
        """以差值調整視窗尺寸並重新渲染圖片

        Args:
            dw: 寬度變化量（px）
            dh: 高度變化量（px）
        """
        new_w = max(20, self.img_w + dw)
        new_h = max(20, self.img_h + dh)
        self._apply_resize(new_w, new_h)
        if self.on_size_change:
            try:
                self.on_size_change(self.overlay_id, self.img_w, self.img_h)
            except Exception:
                pass

    # --------------------------------------------------
    # 公開 API
    # --------------------------------------------------

    def set_alpha(self, alpha: float):
        """即時更新視窗透明度

        Args:
            alpha: 0.1 ~ 1.0
        """
        try:
            self.setWindowOpacity(max(0.1, min(1.0, alpha)))
        except Exception:
            pass

    def update_position(self, x: int, y: int):
        """更新視窗位置

        Args:
            x: 螢幕 X 座標
            y: 螢幕 Y 座標
        """
        try:
            self.move(x, y)
        except Exception:
            pass

    def close(self):
        """關閉視窗並觸發 on_close 回調"""
        if self._closed:
            return
        self._closed = True

        if self._anim_timer.isActive():
            self._anim_timer.stop()

        if self.on_close:
            try:
                self.on_close(self.overlay_id)
            except Exception:
                pass

        super().close()
