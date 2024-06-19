import os
import sys
import time
import random
from datetime import datetime
from pathlib import Path
from typing import Tuple

import cv2
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel,
    QToolBar, QMessageBox, QFileDialog,
    QScrollArea, QSizePolicy, QRubberBand,
    QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QSpinBox,
    QGraphicsDropShadowEffect, QFrame,
)
from PySide6.QtCore import Qt, QSize, QRect, QPoint, Signal
from PySide6.QtGui import QMouseEvent, QPainter, QPen, QIcon, QPixmap, QImage, QTransform, QPalette, qRgb, QColor, QAction, QCursor
import resources



class CustomButton(QWidget):
    clicked = Signal()

    def __init__(
        self,
        icon_path=None,
        text=None,
        icon_size=QSize(24, 24),
        parent=None
    ):
        super().__init__(parent=parent)

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.icon = None
        self.label = None

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Set the icon if provided
        if icon_path:
            pixmap = QPixmap(icon_path).scaled(icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon = QLabel()
            self.icon.setPixmap(pixmap)
            layout.addWidget(self.icon)

        if text:
            self.label = QLabel(text)
            self.label.setStyleSheet("""
                color: white;
            """)
            layout.addWidget(self.label)

        # Set button style
        self.default_style = """
            CustomButton {
                background-color: rgba(78, 65, 232, 255);
                border-radius: 10px;
                font-size: 18px;
                font-weight: 700;
                padding: 10px;
            }
            CustomButton:hover {
                background-color: rgba(67, 56, 202, 255);
            }
        """
        self.inactive_style = """
            CustomButton {
                background-color: rgba(78, 65, 232, 120);
                border-radius: 10px;
                font-size: 18px;
                font-weight: 700;
                padding: 10px;
                opacity: 0.5;
            }
        """

        # Create drop shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(180, 180, 180, 160))
        shadow.setOffset(5, 5)

        # Apply drop shadow effect to the button
        self.setGraphicsEffect(shadow)
        self.setLayout(layout)

        self.active = True
        self.update_style()

    def update_style(self, active=True):
        if active:
            self.setStyleSheet(self.default_style)
            self.setCursor(QCursor(Qt.PointingHandCursor))
        else:
            self.setStyleSheet(self.inactive_style)
            self.setCursor(QCursor(Qt.ForbiddenCursor))

    def disable(self):
        self.active = False
        self.update_style(self.active)

    def enable(self):
        self.active = True
        self.update_style(self.active)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self.active:
            self.clicked.emit()
        return super().mousePressEvent(event)


class ImageLabel(QLabel):
    '''Subclass of QLabel for displaying image'''
    def __init__(self, parent, image=None):
        super().__init__(parent)
        self.parent = parent

        self.original_image = QImage()
        self.image = QImage()
        self.image_copy = QImage()
        self.image_file = None
        self.rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)

        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.setScaledContents(True)

        # Load image
        self.setPixmap(QPixmap().fromImage(self.image))
        self.setAlignment(Qt.Alignment.AlignCenter)

        self.rects = []

    def openImage(self):
        '''Load a new image into the '''
        image_file, _ = QFileDialog.getOpenFileName(self, 'Open Image',
                '', 'JPG Files (*.jpeg *.jpg);;PNG Files (*.png);;Bitmap Files (*.bmp);;\
                GIF Files (*.gif)')

        if image_file:
            self.clear()

            self.image_file = image_file
            # Reset values when opening an image
            self.parent.zoom_factor = 1
            #self.parent.scroll_area.setVisible(True)
            self.parent.updateActions()

            # Reset all sliders
            # self.parent.brightness_slider.setValue(0)

            # Get image format
            self.original_image = QImage(image_file)
            self.image = self.original_image.copy()
            self.image_copy = self.original_image.copy()

            #pixmap = QPixmap(image_file)
            self.setPixmap(QPixmap().fromImage(self.image))
            #image_size = self.image_label.sizeHint()
            self.resize(self.pixmap().size())

            #self.scroll_area.setMinimumSize(image_size)

            #self.image_label.setPixmap(pixmap.scaled(self.image_label.size(),
            #    Qt.KeepAspectRatio, Qt.SmoothTransformation))
        elif image_file == '':
            # User selected Cancel
            pass
        else:
            QMessageBox.information(self, 'Error',
                'Unable to open image.', QMessageBox.Ok)

    def resizeImage(self):
        '''Resize image.'''
        #TODO: Resize image by specified size
        if self.image.isNull() == False:
            resize = QTransform().scale(0.5, 0.5)

            pixmap = QPixmap(self.image)

            resized_image = pixmap.transformed(resize, mode=Qt.SmoothTransformation)

            self.image = QImage(resized_image)
            self.setPixmap(resized_image)
            #self.image = QPixmap(rotated)
            self.setScaledContents(True)
            self.repaint() # repaint the child widget
        else:
            # No image to rotate
            pass

    def clear(self):
        self.image = self.original_image.copy()
        self.image_copy = self.original_image.copy()
        self.rects = []
        self.clear_sidebar()
        self.setPixmap(QPixmap.fromImage(self.image))
        self.repaint()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.origin = event.position().toPoint()
            self.rubber_band.setGeometry(QRect(self.origin, QSize()))
            self.rubber_band.show()

    def mouseMoveEvent(self, event):
        if not self.origin.isNull():
            self.rubber_band.setGeometry(QRect(self.origin, event.position().toPoint()).normalized())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.rubber_band.hide()
            rect = self.rubber_band.geometry()
            if rect.isValid():
                id = len(self.rects)
                self.rects.append(rect)

                image = self.draw_placeholder(self.image_copy, rect, id=id)
                self.setPixmap(QPixmap.fromImage(image))

                pattern_controller = PatternController(id=id, rect=rect)
                pattern_controller.x_changed.connect(self.on_placeholder_x_change)
                pattern_controller.y_changed.connect(self.on_placeholder_y_change)
                pattern_controller.width_changed.connect(self.on_placeholder_width_change)
                pattern_controller.height_changed.connect(self.on_placeholder_height_change)

                self.parent.sidebar_layout.addWidget(pattern_controller)

            if self.rects:
                self.parent.run_button.enable()
                self.parent.export_button.enable()

            self.origin = QPoint()

    def on_placeholder_x_change(self, event):
        id, value = event
        if id < len(self.rects):
            rect = self.rects[id]
            rect = QRect(value, rect.top(), rect.width(), rect.height())
            self.rects[id] = rect

        image = self.redraw_placeholders(self.image.copy(), self.rects)
        self.setPixmap(QPixmap.fromImage(image))

    def on_placeholder_y_change(self, event):
        id, value = event
        if id < len(self.rects):
            rect = self.rects[id]
            rect = QRect(rect.left(), value, rect.width(), rect.height())
            self.rects[id] = rect

        image = self.redraw_placeholders(self.image.copy(), self.rects)
        self.setPixmap(QPixmap.fromImage(image))

    def on_placeholder_width_change(self, event):
        id, value = event
        if id < len(self.rects):
            rect = self.rects[id]
            rect = QRect(rect.left(), rect.top(), value, rect.height())
            self.rects[id] = rect

        image = self.redraw_placeholders(self.image.copy(), self.rects)
        self.setPixmap(QPixmap.fromImage(image))

    def on_placeholder_height_change(self, event):
        id, value = event
        if id < len(self.rects):
            rect = self.rects[id]
            rect = QRect(rect.left(), rect.top(), rect.width(), value)
            self.rects[id] = rect

        image = self.redraw_placeholders(self.image.copy(), self.rects)
        self.setPixmap(QPixmap.fromImage(image))

    def draw_placeholder(self, image, rect, id=None):
        painter = QPainter(image)
        painter.setPen(QPen(Qt.GlobalColor.blue, 2, Qt.PenStyle.SolidLine))
        painter.drawRect(rect)

        # Cross lines
        tr = QPoint(rect.x() + rect.width(), rect.y())
        bl = QPoint(rect.x(), rect.y() + rect.height())
        painter.drawLine(tr, bl)
        painter.drawLine(rect.topLeft(), rect.bottomRight())

        # Placeholder id
        if id is not None:
            tl = rect.topLeft()
            painter.drawText(QPoint(tl.x(), tl.y() - 5), str(id))

        painter.end()
        return image

    def redraw_placeholders(self, image, rects):
        for i, rect in enumerate(rects):
            image = self.draw_placeholder(image, rect, i + 1)
        return image

    def clear_sidebar(self):
        self.delete_all_children(self.parent.sidebar_widget)

    def delete_all_children(self, widget):
        while widget.layout().count():
            child = widget.layout().takeAt(0)
            if child.widget():
                child.widget().deleteLater()


class PhotoEditorGUI(QMainWindow):

    def __init__(self):
        super().__init__()

        self.pattern_files = []

        self.initializeUI()

        self.image = QImage()

    def initializeUI(self):
        self.setWindowTitle('PixStudio')
        self.setMinimumSize(800, 600)
        self.showMaximized()

        self.zoom_factor = 1

        self.init_ui()
        # self.createMenu()
        # self.createToolBar()

        icon_path = ':/icons/icon.png'
        self.setWindowIcon(QIcon(icon_path))

        self.show()

    # def createMenu(self):
    #     '''Set up the menubar.'''

    #     self.exit_act = QAction(QIcon(os.path.join(ICON_DIR, 'exit.png')), 'Quit PixStudio', self)
    #     self.exit_act.setShortcut('Ctrl+Q')
    #     self.exit_act.triggered.connect(self.close)

    #     # Actions for File menu
    #     self.new_act = QAction(QIcon(os.path.join(ICON_DIR, 'new.png')), 'New...')

    #     self.open_act = QAction(QIcon(os.path.join(ICON_DIR, 'open.png')),'Open...', self)
    #     self.open_act.setShortcut('Ctrl+O')
    #     self.open_act.triggered.connect(self.image_label.openImage)

    #     self.zoom_in_act = QAction(QIcon(os.path.join(ICON_DIR, 'zoom_in.png')), 'Zoom In', self)
    #     self.zoom_in_act.setShortcut('Ctrl++')
    #     self.zoom_in_act.triggered.connect(lambda: self.zoomOnImage(1.25))
    #     self.zoom_in_act.setEnabled(False)

    #     self.zoom_out_act = QAction(QIcon(os.path.join(ICON_DIR, 'zoom_out.png')), 'Zoom Out', self)
    #     self.zoom_out_act.setShortcut('Ctrl+-')
    #     self.zoom_out_act.triggered.connect(lambda: self.zoomOnImage(0.8))
    #     self.zoom_out_act.setEnabled(False)

    #     # Actions for Views menu

    #     # Create menubar
    #     menu_bar = self.menuBar()
    #     menu_bar.setNativeMenuBar(False)

    #     # Create file menu and add actions
    #     file_menu = menu_bar.addMenu('File')
    #     file_menu.addAction(self.open_act)

    #     tool_menu = menu_bar.addMenu('Tools')
    #     tool_menu.addSeparator()
    #     tool_menu.addAction(self.zoom_in_act)
    #     tool_menu.addAction(self.zoom_out_act)

    # def createToolBar(self):
    #     '''Set up the toolbar.'''
    #     tool_bar = QToolBar('Main Toolbar')
    #     tool_bar.setIconSize(QSize(26, 26))
    #     self.addToolBar(tool_bar)

    #     # Add actions to the toolbar
    #     tool_bar.addAction(self.open_act)
    #     tool_bar.addAction(self.exit_act)
    #     tool_bar.addSeparator()
    #     tool_bar.addAction(self.zoom_in_act)
    #     tool_bar.addAction(self.zoom_out_act)

    def init_ui(self):
        '''Create an instance of the imageLabel class and set it
           as the main window's central widget.'''
        layout = QVBoxLayout()

        self.top_layout = QVBoxLayout()

        row_widget_1 = QWidget()
        row_layout_1 = QHBoxLayout()
        row_layout_1.setContentsMargins(0, 0, 0, 0)
        row_layout_1.setSpacing(50)
        row_widget_1.setLayout(row_layout_1)

        # icon_path = ':/icons/reset.png'
        # self.reset_button = CustomButton(icon_path=icon_path)
        # self.reset_button.setFixedSize(40, 40)
        # self.reset_button.clicked.connect(self.reset)

        icon_path = ':/icons/add.png'
        self.upload_main_button = CustomButton(icon_path=icon_path, text='Tải ảnh phôi')
        self.upload_main_button.setFixedSize(160, 40)
        self.upload_main_button.clicked.connect(self.upload_main_page)

        icon_path = ':/icons/add.png'
        self.upload_pattern_button = CustomButton(icon_path=icon_path, text='Tải ảnh họa tiết')
        self.upload_pattern_button.setFixedSize(160, 40)
        self.upload_pattern_button.clicked.connect(self.upload_pattern_images)

        icon_path = ':/icons/run.png'
        self.run_button = CustomButton(icon_path=icon_path)
        self.run_button.setFixedSize(40, 40)
        self.run_button.clicked.connect(self.run)
        self.run_button.disable()

        icon_path = ':/icons/export.png'
        self.export_button = CustomButton(icon_path=icon_path, text='Export')
        self.export_button.setFixedSize(160, 40)
        self.export_button.clicked.connect(self.export)
        self.export_button.disable()

        row_layout_1.addStretch(1)
        # row_layout_1.addWidget(self.reset_button)
        row_layout_1.addWidget(self.upload_main_button)
        row_layout_1.addWidget(self.upload_pattern_button)
        row_layout_1.addWidget(self.run_button)
        row_layout_1.addWidget(self.export_button)
        row_layout_1.addStretch(1)

        row_widget_2 = QWidget()
        self.row_layout_2 = QHBoxLayout()
        self.row_layout_2.setContentsMargins(0, 0, 0, 0)
        self.row_layout_2.setSpacing(10)
        self.row_layout_2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row_widget_2.setLayout(self.row_layout_2)

        self.top_layout.addWidget(row_widget_1)
        self.top_layout.addWidget(row_widget_2)

        top_widget = QWidget()
        top_widget.setLayout(self.top_layout)
        top_widget.setFixedHeight(200)

        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout()
        bottom_widget.setLayout(bottom_layout)

        self.sidebar = QScrollArea()
        self.sidebar.setBackgroundRole(QPalette.ColorRole.Dark)
        self.sidebar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sidebar.setFixedWidth(350)
        self.sidebar.setWidgetResizable(True)

        self.sidebar_layout = QVBoxLayout()
        self.sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.sidebar_widget = QWidget()
        self.sidebar_widget.setLayout(self.sidebar_layout)
        self.sidebar.setWidget(self.sidebar_widget)

        self.image_label = ImageLabel(self)
        self.image_label.resize(self.image_label.pixmap().size())

        self.scroll_area = QScrollArea()
        self.scroll_area.setBackgroundRole(QPalette.ColorRole.Dark)
        self.scroll_area.setAlignment(Qt.Alignment.AlignCenter)

        self.scroll_area.setWidget(self.image_label)

        bottom_layout.addWidget(self.sidebar)
        bottom_layout.addWidget(self.scroll_area)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        layout.addWidget(top_widget)
        layout.addWidget(bottom_widget)

    def updateActions(self):
        '''Update the values of menu and toolbar items when an image
        is loaded.'''
        # self.zoom_in_act.setEnabled(True)
        # self.zoom_out_act.setEnabled(True)
        pass

    def reset(self):
        self.image_label.clear()
        self.image_label = ImageLabel(self)
        self.pattern_files = []
        self.repaint()

    def upload_main_page(self):
        self.image_label.openImage()

    def run(self):
        if len(self.pattern_files):
            image = self.composite_pattern_images()
            height, width, channels = image.shape
            bytes_per_line = channels * width
            qimage = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            pixmap = QPixmap.fromImage(qimage)
            self.image_label.setPixmap(pixmap)
        else:
            # Show a message dialog
            QMessageBox.warning(self, 'Không có ảnh họa tiết', 'Vui lòng tải ảnh họa tiết', QMessageBox.Ok)

    def composite_pattern_images(self):
        if len(self.pattern_files):
            image_file = self.image_label.image_file
            image = cv2.imread(image_file)

            rects = self.image_label.rects
            for rect in rects:
                width, height = rect.width(), rect.height()
                cx, cy = rect.center().x(), rect.center().y()

                # Select a pattern randomly
                pattern_file = random.choice(self.pattern_files)
                pattern_image = cv2.imread(pattern_file, cv2.IMREAD_UNCHANGED)

                if pattern_image.ndim == 2:
                    pattern_image = cv2.cvtColor(pattern_image, cv2.COLOR_GRAY2BGR)

                if pattern_image.shape[2] == 3:
                    ph, pw = pattern_image.shape[:2]
                    mask = np.full((pw, ph), fill_value=255, dtype=np.uint8)
                elif pattern_image.shape[2] == 4:
                    mask = pattern_image[:, :, 3]
                    pattern_image = pattern_image[:, :, :3]
                else:
                    return

                ph, pw = pattern_image.shape[:2]
                ratio = max(ph / height, pw / width)

                new_h = int(ph / ratio)
                new_w = int(pw / ratio)

                resized_image = cv2.resize(pattern_image, (new_w, new_h))
                resized_mask = cv2.resize(mask, (new_w, new_h))

                x1, y1 = cx - new_w // 2, cy - new_h // 2
                x2, y2 = x1 + new_w, y1 + new_h

                inv_mask = cv2.bitwise_not(resized_mask)
                cropped_image = image[y1:y2, x1:x2, :].copy()
                cropped_image = cv2.bitwise_and(cropped_image, cropped_image, mask=inv_mask)

                resized_image = cv2.bitwise_and(resized_image, resized_image, mask=resized_mask)
                blended = cv2.add(cropped_image, resized_image)

                image[y1:y2, x1:x2, :] = blended
            return image

    def export(self):
        if len(self.pattern_files):
            image_file = self.image_label.image_file
            image = self.composite_pattern_images()
            if image is None:
                QMessageBox.information(self, 'Thất bại', 'Đã có lỗi xảy ra khi chạy', QMessageBox.Ok)
                return

            # save image
            download_dir = os.path.join('~', 'Downloads')
            output_dir = os.path.expanduser(download_dir)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            output_file = Path(image_file).stem + f'-PixStudio-{timestamp}' + Path(image_file).suffix
            print(output_file)
            file_name = os.path.basename(output_file)
            output_path = os.path.join(output_dir, file_name)
            cv2.imwrite(output_path, image)
            QMessageBox.information(self, 'Thành công', f'Kết quả được lưu tại {output_path}', QMessageBox.Ok)
        else:
            # Show a message dialog
            QMessageBox.warning(self, 'Không có ảnh họa tiết', 'Vui lòng tải ảnh họa tiết', QMessageBox.Ok)

    def upload_pattern_images(self):
        image_files, _ = QFileDialog.getOpenFileNames(self, 'Upload Images',
                '', 'Image Files (*.png *.jpg *.bmp *.gif)')

        if image_files:
            self.pattern_files += image_files

            for image_file in image_files:
                thumbnail_label = QLabel()
                size = 80
                thumbnail_label.setFixedSize(size, size)
                thumbnail_pixmap = QPixmap(image_file).scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio)
                thumbnail_label.setPixmap(thumbnail_pixmap)
                thumbnail_label.setStyleSheet("""
                    border: 1px solid black;
                """)

                self.row_layout_2.addWidget(thumbnail_label)

    def zoomOnImage(self, zoom_value):
        '''Zoom in and zoom out.'''
        self.zoom_factor *= zoom_value
        self.image_label.resize(self.zoom_factor * self.image_label.pixmap().size())

        self.adjustScrollBar(self.scroll_area.horizontalScrollBar(), zoom_value)
        self.adjustScrollBar(self.scroll_area.verticalScrollBar(), zoom_value)

        # self.zoom_in_act.setEnabled(self.zoom_factor < 4.0)
        # self.zoom_out_act.setEnabled(self.zoom_factor > 0.333)

    def adjustScrollBar(self, scroll_bar, value):
        '''Adjust the scrollbar when zooming in or out.'''
        scroll_bar.setValue(int(value * scroll_bar.value()) + ((value - 1) * scroll_bar.pageStep()/2))

    def keyPressEvent(self, event):
        '''Handle key press events.'''
        if event.key() == Qt.Key_Escape:
            self.close()
        if event.key() == Qt.Key_F1: # fn + F1 on Mac
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()

    def closeEvent(self, event):
        pass


class PatternController(QFrame):
    x_changed = Signal(tuple)
    y_changed = Signal(tuple)
    width_changed = Signal(tuple)
    height_changed = Signal(tuple)

    def __init__(self, id=None, rect=None, parent=None):
        super().__init__(parent=parent)

        self.id = id
        self.rect = rect

        self.setObjectName('pattern_controller')
        self.init_ui()

        if self.rect is not None:
            self.spin_box_x.setValue(rect.x())
            self.spin_box_y.setValue(rect.y())
            self.spin_box_width.setValue(rect.width())
            self.spin_box_height.setValue(rect.height())

    def init_ui(self):
        layout = QVBoxLayout()

        # Label
        if self.id is not None:
            text = f'Họa tiết {self.id + 1}'
            label = QLabel(text)
        else:
            label = QLabel()
        label.setStyleSheet('color: black;')

        spin_widget = QWidget()
        spin_layout = QVBoxLayout(spin_widget)

        spin_layout_1 = QHBoxLayout()

        # Create QLabel and QSpinBox for x
        self.label_x = QLabel('X:')
        self.label_x.setStyleSheet('color: black;')
        self.spin_box_x = QSpinBox()
        self.spin_box_x.setRange(0, 1e6)  # Set range from 0 to 100 for example
        self.spin_box_x.valueChanged.connect(self.on_x_changed)

        # Create QLabel and QSpinBox for y
        self.label_y = QLabel('Y:')
        self.label_y.setStyleSheet('color: black;')
        self.spin_box_y = QSpinBox()
        self.spin_box_y.setRange(0, 1e6)  # Set range from 0 to 100 for example
        self.spin_box_y.valueChanged.connect(self.on_y_changed)

        # Add widgets to layout
        spin_layout_1.addWidget(self.label_x)
        spin_layout_1.addWidget(self.spin_box_x)
        spin_layout_1.addWidget(self.label_y)
        spin_layout_1.addWidget(self.spin_box_y)

        spin_layout_2 = QHBoxLayout()
        # Create QLabel and QSpinBox for width
        self.label_width = QLabel('Width:')
        self.label_width.setStyleSheet('color: black;')
        self.spin_box_width = QSpinBox()
        self.spin_box_width.setRange(0, 1e6)  # Set range from 0 to 100 for example
        self.spin_box_width.valueChanged.connect(self.on_width_changed)

        # Create QLabel and QSpinBox for y
        self.label_height = QLabel('Height:')
        self.label_height.setStyleSheet('color: black;')
        self.spin_box_height = QSpinBox()
        self.spin_box_height.setRange(0, 1e6)  # Set range from 0 to 100 for example
        self.spin_box_height.valueChanged.connect(self.on_height_changed)

        # Add widgets to layout
        spin_layout_2.addWidget(self.label_width)
        spin_layout_2.addWidget(self.spin_box_width)
        spin_layout_2.addWidget(self.label_height)
        spin_layout_2.addWidget(self.spin_box_height)

        spin_layout.addLayout(spin_layout_1)
        spin_layout.addLayout(spin_layout_2)

        layout.addWidget(label)
        layout.addWidget(spin_widget)

        self.setLayout(layout)
        self.setStyleSheet("""
            QFrame#pattern_controller {
                border: 1px solid darkgray;
            }
        """)

    def set_x(self, x):
        self.spin_box_x.setValue(x)

    def set_y(self, y):
        self.spin_box_y.setValue(y)

    def on_x_changed(self, value):
        self.x_changed.emit((self.id, value))

    def on_y_changed(self, value):
        self.y_changed.emit((self.id, value))

    def on_width_changed(self, value):
        self.width_changed.emit((self.id, value))

    def on_height_changed(self, value):
        self.height_changed.emit((self.id, value))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PhotoEditorGUI()
    sys.exit(app.exec())