import os
import sys
import time
import random
from datetime import datetime
from pathlib import Path
import cv2
from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel,
    QToolBar, QMessageBox, QFileDialog,
    QScrollArea, QSizePolicy, QRubberBand,
    QVBoxLayout, QHBoxLayout, QWidget, QPushButton,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QSize, QRect, QPoint, Signal
from PySide6.QtGui import QMouseEvent, QPainter, QPen, QIcon, QPixmap, QImage, QTransform, QPalette, qRgb, QColor, QAction, QCursor
import resources

ICON_DIR = 'icons'


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

        self.image = QImage()
        self.image_file = None
        self.rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)

        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.setScaledContents(True)

        # Load image
        self.setPixmap(QPixmap().fromImage(self.image))
        self.setAlignment(Qt.Alignment.AlignCenter)

        self.points = []

    def openImage(self):
        '''Load a new image into the '''
        image_file, _ = QFileDialog.getOpenFileName(self, 'Open Image',
                '', 'PNG Files (*.png);;JPG Files (*.jpeg *.jpg);;Bitmap Files (*.bmp);;\
                GIF Files (*.gif)')

        if image_file:
            self.image_file = image_file
            # Reset values when opening an image
            self.parent.zoom_factor = 1
            #self.parent.scroll_area.setVisible(True)
            self.parent.updateActions()

            # Reset all sliders
            # self.parent.brightness_slider.setValue(0)

            # Get image format
            self.image = QImage(image_file)

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

    def saveImage(self):
        '''Save the image displayed in the label.'''
        #TODO: Add different functionality for the way in which the user can save their image.
        if self.image.isNull() == False:
            image_file, _ = QFileDialog.getSaveFileName(self, 'Save Image',
                '', 'PNG Files (*.png);;JPG Files (*.jpeg *.jpg );;Bitmap Files (*.bmp);;\
                    GIF Files (*.gif)')

            if image_file and self.image.isNull() == False:
                self.image.save(image_file)
            else:
                QMessageBox.information(self, 'Error',
                    'Unable to save image.', QMessageBox.Ok)
        else:
            QMessageBox.information(self, 'Empty Image',
                    'There is no image to save.', QMessageBox.Ok)

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
        self.image = QImage()
        self.image_file = None
        self.points = []
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
                self.points.append(rect)

                painter = QPainter(self.image)
                painter.setPen(QPen(Qt.GlobalColor.blue, 2, Qt.PenStyle.SolidLine))
                painter.drawRect(rect)
                painter.end()
                self.setPixmap(QPixmap.fromImage(self.image))

            if self.points:
                self.parent.export_button.enable()

            self.origin = QPoint()


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

    def createMenu(self):
        '''Set up the menubar.'''

        self.exit_act = QAction(QIcon(os.path.join(ICON_DIR, 'exit.png')), 'Quit PixStudio', self)
        self.exit_act.setShortcut('Ctrl+Q')
        self.exit_act.triggered.connect(self.close)

        # Actions for File menu
        self.new_act = QAction(QIcon(os.path.join(ICON_DIR, 'new.png')), 'New...')

        self.open_act = QAction(QIcon(os.path.join(ICON_DIR, 'open.png')),'Open...', self)
        self.open_act.setShortcut('Ctrl+O')
        self.open_act.triggered.connect(self.image_label.openImage)

        self.zoom_in_act = QAction(QIcon(os.path.join(ICON_DIR, 'zoom_in.png')), 'Zoom In', self)
        self.zoom_in_act.setShortcut('Ctrl++')
        self.zoom_in_act.triggered.connect(lambda: self.zoomOnImage(1.25))
        self.zoom_in_act.setEnabled(False)

        self.zoom_out_act = QAction(QIcon(os.path.join(ICON_DIR, 'zoom_out.png')), 'Zoom Out', self)
        self.zoom_out_act.setShortcut('Ctrl+-')
        self.zoom_out_act.triggered.connect(lambda: self.zoomOnImage(0.8))
        self.zoom_out_act.setEnabled(False)

        # Actions for Views menu

        # Create menubar
        menu_bar = self.menuBar()
        menu_bar.setNativeMenuBar(False)

        # Create file menu and add actions
        file_menu = menu_bar.addMenu('File')
        file_menu.addAction(self.open_act)

        tool_menu = menu_bar.addMenu('Tools')
        tool_menu.addSeparator()
        tool_menu.addAction(self.zoom_in_act)
        tool_menu.addAction(self.zoom_out_act)

    def createToolBar(self):
        '''Set up the toolbar.'''
        tool_bar = QToolBar('Main Toolbar')
        tool_bar.setIconSize(QSize(26, 26))
        self.addToolBar(tool_bar)

        # Add actions to the toolbar
        tool_bar.addAction(self.open_act)
        tool_bar.addAction(self.exit_act)
        tool_bar.addSeparator()
        tool_bar.addAction(self.zoom_in_act)
        tool_bar.addAction(self.zoom_out_act)

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

        # icon_path = os.path.join(ICON_DIR, 'reset.png')
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

        icon_path = ':/icons/export.png'
        self.export_button = CustomButton(icon_path=icon_path, text='Xuất')
        self.export_button.setFixedSize(160, 40)
        self.export_button.clicked.connect(self.export)
        self.export_button.disable()

        row_layout_1.addStretch(1)
        # row_layout_1.addWidget(self.reset_button)
        row_layout_1.addWidget(self.upload_main_button)
        row_layout_1.addWidget(self.upload_pattern_button)
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

        self.image_label = ImageLabel(self)
        self.image_label.resize(self.image_label.pixmap().size())

        self.scroll_area = QScrollArea()
        self.scroll_area.setBackgroundRole(QPalette.ColorRole.Dark)
        self.scroll_area.setAlignment(Qt.Alignment.AlignCenter)

        self.scroll_area.setWidget(self.image_label)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        layout.addWidget(top_widget)
        layout.addWidget(self.scroll_area)

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

    def export(self):
        if len(self.pattern_files):
            image_file = self.image_label.image_file
            image = cv2.imread(image_file)

            points = self.image_label.points
            for rect in points:
                width, height = rect.width(), rect.height()

                # Select a pattern randomly
                pattern_file = random.choice(self.pattern_files)
                pattern_image = cv2.imread(pattern_file)
                resized_image = cv2.resize(pattern_image, (width, height))

                x1, y1 = rect.x(), rect.y()
                x2, y2 = x1 + width, y1 + height
                image[y1:y2, x1:x2, :] = resized_image

            # save image
            output_dir = os.path.expanduser('~/Desktop')
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            output_file = Path(image_file).stem + f'-PixStudio-{timestamp}' + Path(image_file).suffix
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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PhotoEditorGUI()
    sys.exit(app.exec())