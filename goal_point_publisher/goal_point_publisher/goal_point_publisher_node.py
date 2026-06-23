#!/usr/bin/env python3

import math
import sys
from dataclasses import dataclass, asdict

import yaml

import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from rclpy.parameter import Parameter

try:
    from rclpy._rclpy_pybind11 import RCLError
except ImportError:
    RCLError = None

from geometry_msgs.msg import Point

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


# ---------------------------------------------------------------------
# Configuration data
# ---------------------------------------------------------------------

@dataclass
class GoalPublisherConfig:
    minimum_x: float = 0.0
    minimum_y: float = 0.0
    maximum_x: float = 11.08
    maximum_y: float = 11.08
    is_periodic: bool = False

    pub_rate_hz: float = 10.0
    goal_x: float = 5.54
    goal_y: float = 5.54

    display_verbose: bool = True

    window_width: int = 800
    window_height: int = 700


# ---------------------------------------------------------------------
# ROS 2 node
# ---------------------------------------------------------------------

class GoalPointPublisherNode(Node):
    def __init__(self):
        super().__init__('goal_point_publisher')

        self._is_shutting_down = False

        # The only ROS parameter.
        # pub_period is in seconds.
        self.declare_parameter('pub_period', 0.1)

        self.publisher = self.create_publisher(Point, 'goal', 10)

        self.current_goal = Point()
        self.current_goal.x = 5.54
        self.current_goal.y = 5.54
        self.current_goal.z = 0.0

        self.periodic_enabled = False
        self.display_verbose = True
        self.publish_timer = None

        self.set_pub_rate_hz(10.0)

        self.get_logger().info('goal_point_publisher started')

    def set_goal(self, x: float, y: float):
        self.current_goal.x = float(x)
        self.current_goal.y = float(y)
        self.current_goal.z = 0.0

    def set_display_verbose(self, enabled: bool):
        self.display_verbose = bool(enabled)

    def publish_goal(self):
        if self._is_shutting_down:
            return

        self.publisher.publish(self.current_goal)

        if self.display_verbose:
            self.get_logger().info(
                f'Published goal: x={self.current_goal.x:.3f}, '
                f'y={self.current_goal.y:.3f}, z={self.current_goal.z:.3f}'
            )

    def periodic_publish_callback(self):
        if self._is_shutting_down:
            return

        if self.periodic_enabled:
            self.publish_goal()

    def set_periodic_enabled(self, enabled: bool):
        self.periodic_enabled = bool(enabled)

        if self.display_verbose:
            if enabled:
                self.get_logger().info('Periodic publishing enabled')
            else:
                self.get_logger().info('Periodic publishing disabled')

    def set_pub_rate_hz(self, rate_hz: float):
        rate_hz = max(0.1, min(20.0, float(rate_hz)))
        pub_period = 1.0 / rate_hz

        self.set_parameters([
            Parameter(
                'pub_period',
                Parameter.Type.DOUBLE,
                pub_period
            )
        ])

        if self.publish_timer is not None:
            self.publish_timer.cancel()
            self.destroy_timer(self.publish_timer)
            self.publish_timer = None

        self.publish_timer = self.create_timer(
            pub_period,
            self.periodic_publish_callback
        )

        if self.display_verbose:
            self.get_logger().info(
                f'Publishing period set to {pub_period:.4f} s '
                f'({rate_hz:.3f} Hz)'
            )

    def cleanup(self):
        if self._is_shutting_down:
            return

        self._is_shutting_down = True

        self.get_logger().info('Cleaning up...')

        if self.publish_timer is not None:
            self.publish_timer.cancel()
            self.destroy_timer(self.publish_timer)
            self.publish_timer = None

        self.get_logger().info('Cleanup complete')


# ---------------------------------------------------------------------
# Clickable and draggable 2D field widget
# ---------------------------------------------------------------------

class FieldWidget(QWidget):
    goal_changed = pyqtSignal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.minimum_x = 0.0
        self.maximum_x = 11.08
        self.minimum_y = 0.0
        self.maximum_y = 11.08

        self.goal_x = 5.54
        self.goal_y = 5.54

        self.ripples = []
        self.is_dragging_goal = False

        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_ripples)
        self.animation_timer.start(30)

        self.setMinimumSize(250, 250)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.setMouseTracking(True)

    def set_bounds(
        self,
        minimum_x: float,
        maximum_x: float,
        minimum_y: float,
        maximum_y: float,
    ):
        self.minimum_x = float(minimum_x)
        self.maximum_x = float(maximum_x)
        self.minimum_y = float(minimum_y)
        self.maximum_y = float(maximum_y)
        self.update()

    def set_goal(self, x: float, y: float):
        self.goal_x = float(x)
        self.goal_y = float(y)
        self.update()

    def field_rect(self) -> QRectF:
        """
        Return the drawable field rectangle.

        The field preserves world-coordinate scale:
            1 unit in x has the same pixel length as 1 unit in y.

        Therefore:
            drawn_width / drawn_height = x_range / y_range
        """

        margin = 30.0

        available_width = max(1.0, self.width() - 2.0 * margin)
        available_height = max(1.0, self.height() - 2.0 * margin)

        x_range = abs(self.maximum_x - self.minimum_x)
        y_range = abs(self.maximum_y - self.minimum_y)

        if x_range <= 0.0 and y_range <= 0.0:
            aspect_ratio = 1.0
        elif y_range <= 0.0:
            aspect_ratio = 1.0
        else:
            aspect_ratio = x_range / y_range

        available_aspect_ratio = available_width / available_height

        if available_aspect_ratio > aspect_ratio:
            # Available area is too wide; height is limiting.
            field_height = available_height
            field_width = field_height * aspect_ratio
        else:
            # Available area is too tall; width is limiting.
            field_width = available_width
            field_height = field_width / aspect_ratio

        left = (self.width() - field_width) / 2.0
        top = (self.height() - field_height) / 2.0

        return QRectF(left, top, field_width, field_height)

    def grid_cell_size(self) -> float:
        """
        Compute square grid cell size from the smaller world range.

        Formula:
            cell_size = 10^floor(log10(smaller_range)) / 10

        This ensures grid ticks land on clean multiples of 10^n.
        """

        x_range = abs(self.maximum_x - self.minimum_x)
        y_range = abs(self.maximum_y - self.minimum_y)

        smaller_range = min(x_range, y_range)

        if smaller_range <= 0.0:
            return 1.0

        exponent = math.floor(math.log10(smaller_range))
        return (10.0 ** exponent) / 10.0

    def value_to_pixel(self, x: float, y: float) -> QPointF:
        rect = self.field_rect()

        if self.maximum_x == self.minimum_x:
            x_ratio = 0.0
        else:
            x_ratio = (x - self.minimum_x) / (self.maximum_x - self.minimum_x)

        if self.maximum_y == self.minimum_y:
            y_ratio = 0.0
        else:
            y_ratio = (y - self.minimum_y) / (self.maximum_y - self.minimum_y)

        px = rect.left() + x_ratio * rect.width()

        # GUI y-axis points downward.
        # Field y-axis is treated as upward.
        py = rect.bottom() - y_ratio * rect.height()

        return QPointF(px, py)

    def pixel_to_value(self, point: QPointF) -> tuple[float, float]:
        rect = self.field_rect()

        px = min(max(point.x(), rect.left()), rect.right())
        py = min(max(point.y(), rect.top()), rect.bottom())

        if rect.width() <= 0.0:
            x_ratio = 0.0
        else:
            x_ratio = (px - rect.left()) / rect.width()

        if rect.height() <= 0.0:
            y_ratio = 0.0
        else:
            y_ratio = (rect.bottom() - py) / rect.height()

        x = self.minimum_x + x_ratio * (self.maximum_x - self.minimum_x)
        y = self.minimum_y + y_ratio * (self.maximum_y - self.minimum_y)

        return x, y

    def draw_world_grid(self, painter: QPainter, rect: QRectF):
        """
        Draw a square grey grid in world coordinates.

        The grid spacing is the same in x and y. Since field_rect()
        preserves world-coordinate scale, grid cells appear square.
        """

        cell_size = self.grid_cell_size()

        if cell_size <= 0.0:
            return

        painter.save()
        painter.setClipRect(rect)
        painter.setPen(QPen(QColor(220, 220, 220), 1))

        # Vertical grid lines at multiples of cell_size.
        first_x = math.ceil(self.minimum_x / cell_size) * cell_size
        x = first_x

        while x <= self.maximum_x + 1e-9:
            p1 = self.value_to_pixel(x, self.minimum_y)
            p2 = self.value_to_pixel(x, self.maximum_y)

            painter.drawLine(
                int(p1.x()),
                int(p1.y()),
                int(p2.x()),
                int(p2.y())
            )

            x += cell_size

        # Horizontal grid lines at multiples of cell_size.
        first_y = math.ceil(self.minimum_y / cell_size) * cell_size
        y = first_y

        while y <= self.maximum_y + 1e-9:
            p1 = self.value_to_pixel(self.minimum_x, y)
            p2 = self.value_to_pixel(self.maximum_x, y)

            painter.drawLine(
                int(p1.x()),
                int(p1.y()),
                int(p2.x()),
                int(p2.y())
            )

            y += cell_size

        painter.restore()

    def update_goal_from_mouse(
        self,
        point: QPointF,
        create_ripple: bool = False,
    ):
        x, y = self.pixel_to_value(point)

        self.goal_x = x
        self.goal_y = y

        if create_ripple:
            ripple_center = self.value_to_pixel(x, y)

            self.ripples.append({
                'center': ripple_center,
                'radius': 0.0,
                'alpha': 220,
            })

        self.goal_changed.emit(x, y)
        self.update()

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return

        self.is_dragging_goal = True

        self.update_goal_from_mouse(
            QPointF(event.position()),
            create_ripple=True
        )

    def mouseMoveEvent(self, event):
        if not self.is_dragging_goal:
            return

        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return

        self.update_goal_from_mouse(
            QPointF(event.position()),
            create_ripple=False
        )

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return

        self.is_dragging_goal = False

        self.update_goal_from_mouse(
            QPointF(event.position()),
            create_ripple=True
        )

    def leaveEvent(self, event):
        self.is_dragging_goal = False
        super().leaveEvent(event)

    def update_ripples(self):
        if not self.ripples:
            return

        updated = []

        for ripple in self.ripples:
            ripple['radius'] += 6.0
            ripple['alpha'] -= 12

            if ripple['alpha'] > 0:
                updated.append(ripple)

        self.ripples = updated
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.field_rect()

        # Background
        painter.fillRect(self.rect(), QColor(245, 245, 245))

        # Field rectangle
        painter.setPen(QPen(QColor(60, 60, 60), 2))
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawRect(rect)

        # Square world-coordinate grey grid.
        self.draw_world_grid(painter, rect)

        # Boundary labels
        painter.setPen(QPen(QColor(80, 80, 80), 1))
        painter.drawText(
            int(rect.left()),
            int(rect.bottom() + 22),
            f'x: {self.minimum_x:g} → {self.maximum_x:g}'
        )
        painter.drawText(
            int(rect.left()),
            int(rect.top() - 10),
            f'y: {self.minimum_y:g} → {self.maximum_y:g}'
        )

        # Ripples clipped inside field.
        painter.save()
        painter.setClipRect(rect)

        for ripple in self.ripples:
            alpha = max(0, min(255, int(ripple['alpha'])))
            color = QColor(30, 120, 255, alpha)

            painter.setPen(QPen(color, 3))
            painter.setBrush(Qt.BrushStyle.NoBrush)

            center = ripple['center']
            radius = ripple['radius']

            painter.drawEllipse(center, radius, radius)

        painter.restore()

        # Goal point
        goal_pixel = self.value_to_pixel(self.goal_x, self.goal_y)

        painter.setPen(QPen(QColor(20, 80, 200), 2))
        painter.setBrush(QBrush(QColor(30, 120, 255)))
        painter.drawEllipse(goal_pixel, 6, 6)

        # Crosshair
        painter.setPen(QPen(QColor(30, 120, 255), 1))
        painter.drawLine(
            int(goal_pixel.x()),
            int(rect.top()),
            int(goal_pixel.x()),
            int(rect.bottom())
        )
        painter.drawLine(
            int(rect.left()),
            int(goal_pixel.y()),
            int(rect.right()),
            int(goal_pixel.y())
        )


# ---------------------------------------------------------------------
# Main GUI
# ---------------------------------------------------------------------

class GoalPublisherWindow(QMainWindow):
    MIN_RATE_HZ = 0.1
    MAX_RATE_HZ = 20.0

    RATE_SLIDER_MIN = 0
    RATE_SLIDER_MAX = 1000

    COORD_SLIDER_MIN = 0
    COORD_SLIDER_MAX = 1000

    MAIN_PAGE_INDEX = 0
    CONFIG_PAGE_INDEX = 1

    def __init__(self, node: GoalPointPublisherNode):
        super().__init__()

        self.node = node
        self._gui_shutting_down = False

        # Live/applied config.
        self.config = GoalPublisherConfig()

        # Draft config used only on the Config page.
        # Nothing here affects the node until Apply is clicked.
        self.draft_config = GoalPublisherConfig(**asdict(self.config))

        self.previous_goal_x = self.config.goal_x
        self.previous_goal_y = self.config.goal_y

        self.previous_config_values = {
            'minimum_x': self.draft_config.minimum_x,
            'minimum_y': self.draft_config.minimum_y,
            'maximum_x': self.draft_config.maximum_x,
            'maximum_y': self.draft_config.maximum_y,
            'pub_rate_hz': self.draft_config.pub_rate_hz,
        }

        self.setWindowTitle('Goal Point Publisher')
        self.resize(self.config.window_width, self.config.window_height)

        self.build_ui()
        self.apply_live_config_to_main_ui(resize_window=False)

        self.ros_spin_timer = QTimer(self)
        self.ros_spin_timer.timeout.connect(self.spin_ros_once)
        self.ros_spin_timer.start(10)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def build_ui(self):
        root = QWidget()
        root_layout = QVBoxLayout()

        description = QLabel(
            'Publish a geometry_msgs/Point goal by typing coordinates, '
            'using sliders, or clicking/dragging inside the 2D field.'
        )
        description.setWordWrap(True)

        self.stack = QStackedWidget()

        self.main_page = self.build_main_page()
        self.config_page = self.build_config_page()

        self.stack.addWidget(self.main_page)
        self.stack.addWidget(self.config_page)

        root_layout.addWidget(description)
        root_layout.addWidget(self.stack)

        root.setLayout(root_layout)
        self.setCentralWidget(root)

        self.stack.setCurrentIndex(self.MAIN_PAGE_INDEX)

    def build_main_page(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()

        self.boundary_status_label = QLabel()

        self.field_widget = FieldWidget()
        self.field_widget.goal_changed.connect(self.on_field_goal_changed)

        field_group = QGroupBox('2D Field')
        field_layout = QVBoxLayout()
        field_layout.addWidget(self.field_widget)
        field_group.setLayout(field_layout)

        goal_group = QGroupBox('Goal Coordinate')
        goal_layout = QGridLayout()

        self.goal_x_edit = QLineEdit()
        self.goal_y_edit = QLineEdit()

        self.goal_x_slider = QSlider(Qt.Orientation.Horizontal)
        self.goal_y_slider = QSlider(Qt.Orientation.Horizontal)

        self.goal_x_slider.setMinimum(self.COORD_SLIDER_MIN)
        self.goal_x_slider.setMaximum(self.COORD_SLIDER_MAX)

        self.goal_y_slider.setMinimum(self.COORD_SLIDER_MIN)
        self.goal_y_slider.setMaximum(self.COORD_SLIDER_MAX)

        self.goal_x_edit.editingFinished.connect(
            lambda: self.on_goal_text_finished('x')
        )
        self.goal_y_edit.editingFinished.connect(
            lambda: self.on_goal_text_finished('y')
        )

        self.goal_x_slider.valueChanged.connect(
            lambda value: self.on_goal_slider_changed('x', value)
        )
        self.goal_y_slider.valueChanged.connect(
            lambda value: self.on_goal_slider_changed('y', value)
        )

        goal_layout.addWidget(QLabel('x'), 0, 0)
        goal_layout.addWidget(self.goal_x_edit, 0, 1)
        goal_layout.addWidget(self.goal_x_slider, 1, 0, 1, 2)

        goal_layout.addWidget(QLabel('y'), 2, 0)
        goal_layout.addWidget(self.goal_y_edit, 2, 1)
        goal_layout.addWidget(self.goal_y_slider, 3, 0, 1, 2)

        goal_group.setLayout(goal_layout)

        bottom_row = QHBoxLayout()

        self.periodic_radio = QRadioButton()
        self.periodic_radio.setAutoExclusive(False)
        self.periodic_radio.toggled.connect(self.on_periodic_toggled)

        self.publish_button = QPushButton('Publish')
        self.publish_button.clicked.connect(self.on_publish_clicked)

        self.config_button = QPushButton('Config')
        self.config_button.clicked.connect(self.on_config_button_clicked)

        bottom_row.addWidget(self.periodic_radio)
        bottom_row.addStretch()
        bottom_row.addWidget(self.publish_button)
        bottom_row.addWidget(self.config_button)
        bottom_row.addStretch()

        layout.addWidget(self.boundary_status_label)
        layout.addWidget(field_group, stretch=1)
        layout.addWidget(goal_group)
        layout.addLayout(bottom_row)

        widget.setLayout(layout)
        return widget

    def build_config_page(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()

        boundary_group = QGroupBox('Boundary Configuration')
        boundary_layout = QFormLayout()

        self.minimum_x_edit = QLineEdit()
        self.minimum_y_edit = QLineEdit()
        self.maximum_x_edit = QLineEdit()
        self.maximum_y_edit = QLineEdit()

        self.minimum_x_edit.editingFinished.connect(
            lambda: self.validate_config_boundary_field('minimum_x')
        )
        self.minimum_y_edit.editingFinished.connect(
            lambda: self.validate_config_boundary_field('minimum_y')
        )
        self.maximum_x_edit.editingFinished.connect(
            lambda: self.validate_config_boundary_field('maximum_x')
        )
        self.maximum_y_edit.editingFinished.connect(
            lambda: self.validate_config_boundary_field('maximum_y')
        )

        self.config_periodic_check = QCheckBox('Periodic publishing by default')
        self.config_verbose_check = QCheckBox('Display publishing verbose')

        boundary_layout.addRow('minimum_x', self.minimum_x_edit)
        boundary_layout.addRow('minimum_y', self.minimum_y_edit)
        boundary_layout.addRow('maximum_x', self.maximum_x_edit)
        boundary_layout.addRow('maximum_y', self.maximum_y_edit)
        boundary_layout.addRow('is_periodic', self.config_periodic_check)
        boundary_layout.addRow('display_verbose', self.config_verbose_check)

        boundary_group.setLayout(boundary_layout)

        rate_group = QGroupBox('Publishing Rate')
        rate_layout = QGridLayout()

        self.rate_edit = QLineEdit()
        self.rate_slider = QSlider(Qt.Orientation.Horizontal)

        self.rate_slider.setMinimum(self.RATE_SLIDER_MIN)
        self.rate_slider.setMaximum(self.RATE_SLIDER_MAX)

        self.rate_edit.editingFinished.connect(self.on_rate_text_finished)
        self.rate_slider.valueChanged.connect(self.on_rate_slider_changed)

        rate_layout.addWidget(QLabel('Rate [Hz]'), 0, 0)
        rate_layout.addWidget(self.rate_edit, 0, 1)
        rate_layout.addWidget(self.rate_slider, 1, 0, 1, 2)

        rate_group.setLayout(rate_layout)

        button_row = QHBoxLayout()

        self.apply_button = QPushButton('Apply')
        self.save_button = QPushButton('Save')
        self.load_button = QPushButton('Load')

        self.apply_button.clicked.connect(self.on_apply_config_clicked)
        self.save_button.clicked.connect(self.save_config_file)
        self.load_button.clicked.connect(self.load_config_file)

        button_row.addStretch()
        button_row.addWidget(self.apply_button)
        button_row.addWidget(self.save_button)
        button_row.addWidget(self.load_button)

        layout.addWidget(boundary_group)
        layout.addWidget(rate_group)
        layout.addStretch()
        layout.addLayout(button_row)

        widget.setLayout(layout)
        return widget

    # ------------------------------------------------------------------
    # ROS integration and shutdown handling
    # ------------------------------------------------------------------

    def spin_ros_once(self):
        if self._gui_shutting_down:
            return

        if not rclpy.ok():
            self.request_gui_shutdown()
            return

        try:
            rclpy.spin_once(self.node, timeout_sec=0.0)

        except ExternalShutdownException:
            self.request_gui_shutdown()

        except Exception as e:
            is_rcl_error = RCLError is not None and isinstance(e, RCLError)

            if is_rcl_error or not rclpy.ok() or 'context is not valid' in str(e):
                self.request_gui_shutdown()
                return

            raise

    def request_gui_shutdown(self):
        if self._gui_shutting_down:
            return

        self._gui_shutting_down = True

        if hasattr(self, 'ros_spin_timer') and self.ros_spin_timer.isActive():
            self.ros_spin_timer.stop()

        self.close()

        app = QApplication.instance()
        if app is not None:
            app.quit()

    def closeEvent(self, event):
        self._gui_shutting_down = True

        if hasattr(self, 'ros_spin_timer') and self.ros_spin_timer.isActive():
            self.ros_spin_timer.stop()

        super().closeEvent(event)

    # ------------------------------------------------------------------
    # Config page behavior
    # ------------------------------------------------------------------

    def on_config_button_clicked(self):
        self.draft_config = GoalPublisherConfig(**asdict(self.config))
        self.load_draft_config_into_config_ui()
        self.stack.setCurrentIndex(self.CONFIG_PAGE_INDEX)

    def load_draft_config_into_config_ui(self):
        self.minimum_x_edit.setText(str(self.draft_config.minimum_x))
        self.minimum_y_edit.setText(str(self.draft_config.minimum_y))
        self.maximum_x_edit.setText(str(self.draft_config.maximum_x))
        self.maximum_y_edit.setText(str(self.draft_config.maximum_y))

        self.config_periodic_check.setChecked(self.draft_config.is_periodic)
        self.config_verbose_check.setChecked(self.draft_config.display_verbose)

        self.set_rate_config_ui(self.draft_config.pub_rate_hz)

        self.previous_config_values = {
            'minimum_x': self.draft_config.minimum_x,
            'minimum_y': self.draft_config.minimum_y,
            'maximum_x': self.draft_config.maximum_x,
            'maximum_y': self.draft_config.maximum_y,
            'pub_rate_hz': self.draft_config.pub_rate_hz,
        }

    def on_apply_config_clicked(self):
        if not self.validate_all_config_fields():
            return

        self.draft_config.minimum_x = float(self.minimum_x_edit.text())
        self.draft_config.minimum_y = float(self.minimum_y_edit.text())
        self.draft_config.maximum_x = float(self.maximum_x_edit.text())
        self.draft_config.maximum_y = float(self.maximum_y_edit.text())
        self.draft_config.is_periodic = self.config_periodic_check.isChecked()
        self.draft_config.display_verbose = self.config_verbose_check.isChecked()
        self.draft_config.pub_rate_hz = self.clamp_rate(
            float(self.rate_edit.text())
        )

        self.draft_config.goal_x = self.clamp(
            self.config.goal_x,
            self.draft_config.minimum_x,
            self.draft_config.maximum_x
        )
        self.draft_config.goal_y = self.clamp(
            self.config.goal_y,
            self.draft_config.minimum_y,
            self.draft_config.maximum_y
        )

        self.draft_config.window_width = self.width()
        self.draft_config.window_height = self.height()

        self.config = GoalPublisherConfig(**asdict(self.draft_config))

        self.apply_live_config_to_main_ui(resize_window=False)
        self.stack.setCurrentIndex(self.MAIN_PAGE_INDEX)

    def apply_live_config_to_main_ui(self, resize_window: bool = True):
        self.boundary_status_label.setText(
            f'Boundary: '
            f'x=[{self.config.minimum_x}, {self.config.maximum_x}], '
            f'y=[{self.config.minimum_y}, {self.config.maximum_y}]'
        )

        self.config.goal_x = self.clamp(
            self.config.goal_x,
            self.config.minimum_x,
            self.config.maximum_x
        )
        self.config.goal_y = self.clamp(
            self.config.goal_y,
            self.config.minimum_y,
            self.config.maximum_y
        )

        self.field_widget.set_bounds(
            self.config.minimum_x,
            self.config.maximum_x,
            self.config.minimum_y,
            self.config.maximum_y,
        )

        self.set_goal_ui('x', self.config.goal_x)
        self.set_goal_ui('y', self.config.goal_y)

        self.node.set_display_verbose(self.config.display_verbose)
        self.node.set_pub_rate_hz(self.config.pub_rate_hz)

        self.periodic_radio.setChecked(self.config.is_periodic)
        self.on_periodic_toggled(self.config.is_periodic)

        self.update_periodic_radio_text()

        self.node.set_goal(self.config.goal_x, self.config.goal_y)
        self.field_widget.set_goal(self.config.goal_x, self.config.goal_y)

        if resize_window:
            self.resize(self.config.window_width, self.config.window_height)

    # ------------------------------------------------------------------
    # Config validation
    # ------------------------------------------------------------------

    def validate_all_config_fields(self) -> bool:
        self.validate_config_boundary_field('minimum_x')
        self.validate_config_boundary_field('minimum_y')
        self.validate_config_boundary_field('maximum_x')
        self.validate_config_boundary_field('maximum_y')
        self.on_rate_text_finished()

        return True

    def validate_config_boundary_field(self, key: str):
        edit_map = {
            'minimum_x': self.minimum_x_edit,
            'minimum_y': self.minimum_y_edit,
            'maximum_x': self.maximum_x_edit,
            'maximum_y': self.maximum_y_edit,
        }

        line_edit = edit_map[key]

        try:
            value = float(line_edit.text().strip())
        except ValueError:
            value = self.previous_config_values[key]
            line_edit.setText(str(value))
            QMessageBox.warning(
                self,
                'Invalid boundary value',
                f'{key} must be numeric. Reverting to previous value.'
            )
            return

        self.previous_config_values[key] = value

        try:
            minimum_x = float(self.minimum_x_edit.text())
            minimum_y = float(self.minimum_y_edit.text())
            maximum_x = float(self.maximum_x_edit.text())
            maximum_y = float(self.maximum_y_edit.text())
        except ValueError:
            return

        if minimum_x > maximum_x:
            if key == 'minimum_x':
                minimum_x = maximum_x
                self.minimum_x_edit.setText(str(minimum_x))
                self.previous_config_values['minimum_x'] = minimum_x
            else:
                maximum_x = minimum_x
                self.maximum_x_edit.setText(str(maximum_x))
                self.previous_config_values['maximum_x'] = maximum_x

            QMessageBox.warning(
                self,
                'Invalid x range',
                'The x range must be proper: minimum_x cannot be greater '
                'than maximum_x.'
            )

        if minimum_y > maximum_y:
            if key == 'minimum_y':
                minimum_y = maximum_y
                self.minimum_y_edit.setText(str(minimum_y))
                self.previous_config_values['minimum_y'] = minimum_y
            else:
                maximum_y = minimum_y
                self.maximum_y_edit.setText(str(maximum_y))
                self.previous_config_values['maximum_y'] = maximum_y

            QMessageBox.warning(
                self,
                'Invalid y range',
                'The y range must be proper: minimum_y cannot be greater '
                'than maximum_y.'
            )

    # ------------------------------------------------------------------
    # YAML load/save
    # ------------------------------------------------------------------

    def load_config_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            'Load Configuration File',
            '',
            'YAML Files (*.yaml *.yml);;All Files (*)'
        )

        if not filename:
            return

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if data is None:
                data = {}

            loaded = GoalPublisherConfig(
                minimum_x=float(data.get('minimum_x', 0.0)),
                minimum_y=float(data.get('minimum_y', 0.0)),
                maximum_x=float(data.get('maximum_x', 11.08)),
                maximum_y=float(data.get('maximum_y', 11.08)),
                is_periodic=bool(data.get('is_periodic', False)),
                pub_rate_hz=float(data.get('pub_rate_hz', 10.0)),
                goal_x=float(data.get('goal_x', self.config.goal_x)),
                goal_y=float(data.get('goal_y', self.config.goal_y)),
                display_verbose=bool(data.get('display_verbose', True)),
                window_width=int(data.get('window_width', 800)),
                window_height=int(data.get('window_height', 700)),
            )

            if loaded.minimum_x > loaded.maximum_x:
                loaded.minimum_x = loaded.maximum_x
                QMessageBox.warning(
                    self,
                    'Invalid x range',
                    'Loaded minimum_x was greater than maximum_x. '
                    'minimum_x was adjusted to maximum_x.'
                )

            if loaded.minimum_y > loaded.maximum_y:
                loaded.minimum_y = loaded.maximum_y
                QMessageBox.warning(
                    self,
                    'Invalid y range',
                    'Loaded minimum_y was greater than maximum_y. '
                    'minimum_y was adjusted to maximum_y.'
                )

            loaded.pub_rate_hz = self.clamp_rate(loaded.pub_rate_hz)
            loaded.goal_x = self.clamp(
                loaded.goal_x,
                loaded.minimum_x,
                loaded.maximum_x
            )
            loaded.goal_y = self.clamp(
                loaded.goal_y,
                loaded.minimum_y,
                loaded.maximum_y
            )

            loaded.window_width = max(400, loaded.window_width)
            loaded.window_height = max(400, loaded.window_height)

            self.draft_config = loaded
            self.load_draft_config_into_config_ui()

            QMessageBox.information(
                self,
                'Configuration loaded',
                'Configuration loaded into the Config page.\n'
                'Click Apply to use it.'
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                'Load failed',
                f'Failed to load configuration file:\n{e}'
            )

    def save_config_file(self):
        if not self.validate_all_config_fields():
            return

        temp_config = GoalPublisherConfig(
            minimum_x=float(self.minimum_x_edit.text()),
            minimum_y=float(self.minimum_y_edit.text()),
            maximum_x=float(self.maximum_x_edit.text()),
            maximum_y=float(self.maximum_y_edit.text()),
            is_periodic=self.config_periodic_check.isChecked(),
            pub_rate_hz=self.clamp_rate(float(self.rate_edit.text())),
            goal_x=self.config.goal_x,
            goal_y=self.config.goal_y,
            display_verbose=self.config_verbose_check.isChecked(),
            window_width=self.width(),
            window_height=self.height(),
        )

        filename, _ = QFileDialog.getSaveFileName(
            self,
            'Save Configuration File',
            'goal_point_config.yaml',
            'YAML Files (*.yaml *.yml);;All Files (*)'
        )

        if not filename:
            return

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                yaml.safe_dump(
                    asdict(temp_config),
                    f,
                    sort_keys=False,
                    default_flow_style=False
                )

            QMessageBox.information(
                self,
                'Configuration saved',
                'Configuration saved successfully.'
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                'Save failed',
                f'Failed to save configuration file:\n{e}'
            )

    # ------------------------------------------------------------------
    # Goal coordinate textbox + linear slider + field click/drag
    # ------------------------------------------------------------------

    def on_field_goal_changed(self, x: float, y: float):
        self.set_goal_ui('x', x)
        self.set_goal_ui('y', y)
        self.node.set_goal(self.config.goal_x, self.config.goal_y)
        self.field_widget.set_goal(self.config.goal_x, self.config.goal_y)

    def on_goal_text_finished(self, axis: str):
        if axis == 'x':
            line_edit = self.goal_x_edit
            previous_value = self.previous_goal_x
            lower = self.config.minimum_x
            upper = self.config.maximum_x
        else:
            line_edit = self.goal_y_edit
            previous_value = self.previous_goal_y
            lower = self.config.minimum_y
            upper = self.config.maximum_y

        try:
            value = float(line_edit.text().strip())
        except ValueError:
            value = previous_value
            QMessageBox.warning(
                self,
                'Invalid goal value',
                f'Goal {axis} must be numeric. Reverting to previous value.'
            )

        clamped_value = self.clamp(value, lower, upper)

        if clamped_value != value:
            QMessageBox.warning(
                self,
                'Goal outside boundary',
                f'Goal {axis} must be inside [{lower}, {upper}]. '
                f'Using nearest limit: {clamped_value}.'
            )

        self.set_goal_ui(axis, clamped_value)
        self.node.set_goal(self.config.goal_x, self.config.goal_y)
        self.field_widget.set_goal(self.config.goal_x, self.config.goal_y)

    def on_goal_slider_changed(self, axis: str, slider_value: int):
        value = self.coord_slider_to_value(axis, slider_value)
        self.set_goal_ui(axis, value, update_slider=False)
        self.node.set_goal(self.config.goal_x, self.config.goal_y)
        self.field_widget.set_goal(self.config.goal_x, self.config.goal_y)

    def set_goal_ui(
        self,
        axis: str,
        value: float,
        update_slider: bool = True
    ):
        if axis == 'x':
            value = self.clamp(
                value,
                self.config.minimum_x,
                self.config.maximum_x
            )

            self.config.goal_x = value
            self.previous_goal_x = value

            self.goal_x_edit.blockSignals(True)
            self.goal_x_edit.setText(f'{value:.4f}')
            self.goal_x_edit.blockSignals(False)

            if update_slider:
                slider_value = self.coord_value_to_slider('x', value)

                self.goal_x_slider.blockSignals(True)
                self.goal_x_slider.setValue(slider_value)
                self.goal_x_slider.blockSignals(False)

        else:
            value = self.clamp(
                value,
                self.config.minimum_y,
                self.config.maximum_y
            )

            self.config.goal_y = value
            self.previous_goal_y = value

            self.goal_y_edit.blockSignals(True)
            self.goal_y_edit.setText(f'{value:.4f}')
            self.goal_y_edit.blockSignals(False)

            if update_slider:
                slider_value = self.coord_value_to_slider('y', value)

                self.goal_y_slider.blockSignals(True)
                self.goal_y_slider.setValue(slider_value)
                self.goal_y_slider.blockSignals(False)

    def coord_value_to_slider(self, axis: str, value: float) -> int:
        if axis == 'x':
            lower = self.config.minimum_x
            upper = self.config.maximum_x
        else:
            lower = self.config.minimum_y
            upper = self.config.maximum_y

        if upper == lower:
            return self.COORD_SLIDER_MIN

        ratio = (value - lower) / (upper - lower)

        return int(
            self.COORD_SLIDER_MIN
            + ratio * (self.COORD_SLIDER_MAX - self.COORD_SLIDER_MIN)
        )

    def coord_slider_to_value(self, axis: str, slider_value: int) -> float:
        if axis == 'x':
            lower = self.config.minimum_x
            upper = self.config.maximum_x
        else:
            lower = self.config.minimum_y
            upper = self.config.maximum_y

        ratio = (
            (slider_value - self.COORD_SLIDER_MIN)
            / (self.COORD_SLIDER_MAX - self.COORD_SLIDER_MIN)
        )

        return lower + ratio * (upper - lower)

    # ------------------------------------------------------------------
    # Publishing rate textbox + logarithmic slider
    # Config UI only. Does not affect live ROS node until Apply.
    # ------------------------------------------------------------------

    def on_rate_text_finished(self):
        try:
            rate = float(self.rate_edit.text().strip())
        except ValueError:
            rate = self.previous_config_values['pub_rate_hz']
            QMessageBox.warning(
                self,
                'Invalid rate',
                'Publishing rate must be numeric. Reverting to previous value.'
            )

        rate = self.clamp_rate(rate)
        self.set_rate_config_ui(rate)

    def on_rate_slider_changed(self, slider_value: int):
        rate = self.rate_slider_to_value(slider_value)
        self.set_rate_config_ui(rate, update_slider=False)

    def set_rate_config_ui(
        self,
        rate_hz: float,
        update_slider: bool = True
    ):
        rate_hz = self.clamp_rate(rate_hz)
        self.previous_config_values['pub_rate_hz'] = rate_hz

        self.rate_edit.blockSignals(True)
        self.rate_edit.setText(f'{rate_hz:.3f}')
        self.rate_edit.blockSignals(False)

        if update_slider:
            slider_value = self.rate_value_to_slider(rate_hz)

            self.rate_slider.blockSignals(True)
            self.rate_slider.setValue(slider_value)
            self.rate_slider.blockSignals(False)

    def rate_slider_to_value(self, slider_value: int) -> float:
        ratio = (
            (slider_value - self.RATE_SLIDER_MIN)
            / (self.RATE_SLIDER_MAX - self.RATE_SLIDER_MIN)
        )

        return self.MIN_RATE_HZ * (
            self.MAX_RATE_HZ / self.MIN_RATE_HZ
        ) ** ratio

    def rate_value_to_slider(self, rate_hz: float) -> int:
        rate_hz = self.clamp_rate(rate_hz)

        ratio = math.log(rate_hz / self.MIN_RATE_HZ) / math.log(
            self.MAX_RATE_HZ / self.MIN_RATE_HZ
        )

        return int(
            self.RATE_SLIDER_MIN
            + ratio * (self.RATE_SLIDER_MAX - self.RATE_SLIDER_MIN)
        )

    def clamp_rate(self, rate_hz: float) -> float:
        return self.clamp(rate_hz, self.MIN_RATE_HZ, self.MAX_RATE_HZ)

    # ------------------------------------------------------------------
    # Publish controls
    # ------------------------------------------------------------------

    def on_publish_clicked(self):
        self.on_goal_text_finished('x')
        self.on_goal_text_finished('y')
        self.node.publish_goal()

    def on_periodic_toggled(self, checked: bool):
        self.config.is_periodic = checked
        self.publish_button.setEnabled(not checked)
        self.node.set_periodic_enabled(checked)
        self.update_periodic_radio_text()

    def update_periodic_radio_text(self):
        self.periodic_radio.setText(
            f'Periodic {self.config.pub_rate_hz:.3f} Hz'
        )

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def clamp(value: float, lower: float, upper: float) -> float:
        return max(lower, min(upper, value))


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main(args=None):
    rclpy.init(args=args)

    node = GoalPointPublisherNode()

    app = QApplication(sys.argv)
    window = GoalPublisherWindow(node)
    window.show()

    try:
        app.exec()

    except KeyboardInterrupt:
        node.get_logger().info('Keyboard interrupt received')

    except ExternalShutdownException:
        pass

    finally:
        node.cleanup()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()