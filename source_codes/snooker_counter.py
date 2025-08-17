import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QGridLayout, QLabel, QPushButton, QSpinBox, QMessageBox,
    QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

BALL_COLORS = {
    "red": 1, "yellow": 2, "green": 3, "brown": 4, "blue": 5, "pink": 6, "black": 7
}
FOUL_VALUES = [4, 5, 6, 7]
RED_BALLS_INITIAL = 15
MAX_SCORE = 999
BALL_SIZE = 24
SPACING_DEFAULT = 10
SPACING_SMALL = 8
SPACING_LARGE = 15

STYLESHEET_NAME = "style.qss"
ICON_NAME = "snooker_icon.png"

class SnookerScorerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Snooker Counter")
        self.setGeometry(100, 100, 350, 450)

        self.last_ball_color = None

        self._load_icon()
        self.init_ui()
        self._apply_styles(STYLESHEET_NAME)
        self.calculate_score()

    def _load_icon(self):
        """Loads the window icon."""
        try:
            base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(base_path, ICON_NAME)
            self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"Error loading icon: {e}")

    def init_ui(self):
        """Initializes the user interface."""
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(SPACING_DEFAULT)

        score_input_group_layout = QVBoxLayout()
        score_input_group_layout.setSpacing(SPACING_DEFAULT)

        self.red_balls_spinbox = self._create_spinbox("Number of red balls:", RED_BALLS_INITIAL, 0, RED_BALLS_INITIAL)
        score_input_group_layout.addLayout(self._create_hbox_with_widget("Number of reds:", self.red_balls_spinbox))

        self.player1_score_spinbox = self._create_spinbox("Player 1 score:", 0, 0, MAX_SCORE)
        score_input_group_layout.addLayout(self._create_hbox_with_widget("Player 1’s points:", self.player1_score_spinbox))

        self.player2_score_spinbox = self._create_spinbox("Player 2 score:", 0, 0, MAX_SCORE)
        score_input_group_layout.addLayout(self._create_hbox_with_widget("Player 2’s points:", self.player2_score_spinbox))

        main_layout.addLayout(score_input_group_layout)

        reset_button = QPushButton("New frame / Reset")
        reset_button.setObjectName("resetButton")
        reset_button.clicked.connect(self.reset_game_state)
        main_layout.addWidget(reset_button)

        players_main_grid_layout = QGridLayout()
        players_main_grid_layout.setSpacing(SPACING_LARGE)

        players_main_grid_layout.addLayout(self._create_player_section("Player 1", self.player1_score_spinbox, self.player2_score_spinbox), 0, 0)
        players_main_grid_layout.addLayout(self._create_player_section("Player 2", self.player2_score_spinbox, self.player1_score_spinbox), 1, 0)

        main_layout.addLayout(players_main_grid_layout)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(separator)

        main_layout.addWidget(QLabel("Colours on table:"))
        color_balls_layout = QHBoxLayout()
        color_balls_layout.setSpacing(SPACING_SMALL)
        self.color_ball_buttons = []
        for color, value in [(c,v) for c,v in BALL_COLORS.items() if c != 'red']:
            btn = self._create_ball_button(color, value, is_toggle=True)
            btn.clicked.connect(lambda checked, b=btn: self.toggle_color_ball(b))
            self.color_ball_buttons.append(btn)
            color_balls_layout.addWidget(btn)
        main_layout.addLayout(color_balls_layout)

        self.result_label = QLabel("Difference: 0; Remaining: 0")
        self.result_label.setObjectName("resultLabel")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.result_label)

        footer_label = QLabel("2025 Underdog Guild")
        footer_label.setObjectName("footerLabel")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(footer_label)

    def _create_hbox_with_widget(self, label_text: str, widget: QWidget) -> QHBoxLayout:
        """Creates a QHBoxLayout with a QLabel and a widget."""
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel(label_text))
        h_layout.addWidget(widget)
        return h_layout

    def _create_spinbox(self, label_text: str, initial_value: int, min_value: int, max_value: int) -> QSpinBox:
        """Creates and configures a QSpinBox."""
        spinbox = QSpinBox()
        spinbox.setRange(min_value, max_value)
        spinbox.setValue(initial_value)
        spinbox.valueChanged.connect(self.calculate_score)
        return spinbox

    def _create_ball_button(self, color: str, value: int, is_toggle: bool = False) -> QPushButton:
        """Creates and configures a ball button."""
        btn = QPushButton("")
        btn.setFixedSize(BALL_SIZE, BALL_SIZE)
        btn.setProperty("color", color)
        btn.setProperty("value", value)
        btn.setProperty("class_status", "ball")
        if is_toggle:
            btn.setProperty("inactive", False)
        return btn

    def _create_foul_buttons(self, target_score_spinbox: QSpinBox) -> QHBoxLayout:
        """Creates foul buttons for a player."""
        foul_layout = QHBoxLayout()
        foul_layout.setSpacing(SPACING_SMALL)
        for foul_val in FOUL_VALUES:
            btn = QPushButton(f"Foul {foul_val}")
            btn.setProperty("class_status", "foul_btn")
            btn.clicked.connect(lambda checked, val=foul_val: self.add_foul_points(target_score_spinbox, val))
            foul_layout.addWidget(btn)
        return foul_layout

    def _create_player_ball_grid(self, player_score_spinbox: QSpinBox) -> QGridLayout:
        """Creates the grid of potted balls for a player."""
        balls_grid = QGridLayout()
        balls_grid.setSpacing(SPACING_SMALL)
        player_ball_buttons = []

        red_pb = self._create_ball_button("red", BALL_COLORS["red"])
        red_pb.clicked.connect(lambda checked, b=red_pb: self.add_player_score(b, player_score_spinbox))
        player_ball_buttons.append(red_pb)
        balls_grid.addWidget(red_pb, 0, 0)

        col_idx = 1
        for color, value in [(c,v) for c,v in BALL_COLORS.items() if c != 'red']:
            color_pb = self._create_ball_button(color, value)
            color_pb.clicked.connect(lambda checked, b=color_pb: self.add_player_score(b, player_score_spinbox))
            player_ball_buttons.append(color_pb)
            balls_grid.addWidget(color_pb, 0, col_idx)
            col_idx += 1

        free_pb = QPushButton("FREE")
        free_pb.setFixedSize(BALL_SIZE, BALL_SIZE)
        free_pb.setProperty("color", "free")
        free_pb.setProperty("value", BALL_COLORS["red"])
        free_pb.setProperty("class_status", "ball")
        free_pb.clicked.connect(lambda checked, b=free_pb: self.add_player_score(b, player_score_spinbox))
        player_ball_buttons.append(free_pb)
        balls_grid.addWidget(free_pb, 0, col_idx)

        if player_score_spinbox == self.player1_score_spinbox:
            self.player1_ball_buttons = player_ball_buttons
        else:
            self.player2_ball_buttons = player_ball_buttons

        return balls_grid

    def _create_player_section(self, player_label_text: str, player_score_spinbox: QSpinBox, opponent_score_spinbox: QSpinBox) -> QVBoxLayout:
        """Creates a player's section (potted balls and foul buttons)."""
        player_section_layout = QVBoxLayout()
        player_section_layout.addWidget(QLabel(f"{player_label_text} potted balls:"))
        player_section_layout.addLayout(self._create_player_ball_grid(player_score_spinbox))
        player_section_layout.addLayout(self._create_foul_buttons(opponent_score_spinbox))
        return player_section_layout

    def reset_game_state(self):
        """Resets the game state for a new frame."""
        self.player1_score_spinbox.setValue(0)
        self.player2_score_spinbox.setValue(0)
        self.red_balls_spinbox.setValue(RED_BALLS_INITIAL)
        self.last_ball_color = None

        for ball_button in self.color_ball_buttons:
            ball_button.setProperty("inactive", False)
            ball_button.style().polish(ball_button)

        self.calculate_score()

    def add_foul_points(self, target_player_score_spinbox: QSpinBox, foul_value: int):
        """Adds foul points to the target player's score."""
        target_player_score_spinbox.setValue(target_player_score_spinbox.value() + foul_value)
        self.last_ball_color = None
        self.calculate_score()

    def toggle_color_ball(self, ball_button: QPushButton):
        """Toggles the inactive state of a color ball on the table."""
        is_inactive = ball_button.property("inactive")
        ball_button.setProperty("inactive", not is_inactive)
        ball_button.style().polish(ball_button)
        self.calculate_score()

    def add_player_score(self, ball_button: QPushButton, player_score_spinbox: QSpinBox):
        """Adds the potted ball's points to the player's score."""
        value = int(ball_button.property("value"))
        color = ball_button.property("color")
        current_red_balls = self.red_balls_spinbox.value()

        if color == 'red':
            if current_red_balls > 0:
                self.red_balls_spinbox.setValue(current_red_balls - 1)
                player_score_spinbox.setValue(player_score_spinbox.value() + value)
                self.last_ball_color = color
            else:
                QMessageBox.warning(self, "Error", "There are no more reds on the table!")
                return
        elif color == 'free':
            if current_red_balls > 0:
                player_score_spinbox.setValue(player_score_spinbox.value() + value)
                self.last_ball_color = color
            else:
                QMessageBox.warning(self, "Error", "There are no more reds on the table!")
                return
        else:
            ball_on_table_inactive = True
            for cb in self.color_ball_buttons:
                if cb.property("color") == color:
                    ball_on_table_inactive = cb.property("inactive")
                    break

            if ball_on_table_inactive:
                QMessageBox.warning(self, "Error", f"The {color} ball is already off the table!")
                return
            
            player_score_spinbox.setValue(player_score_spinbox.value() + value)
            self.last_ball_color = color

        self.update_ball_states()
        self.calculate_score()

    def update_ball_states(self):
        """Updates the state of the ball buttons according to game rules."""
        red_balls_remaining = self.red_balls_spinbox.value()
        all_player_buttons = self.player1_ball_buttons + self.player2_ball_buttons

        for ball_button in all_player_buttons:
            color = ball_button.property("color")
            is_inactive = False

            if red_balls_remaining == 0:
                if color in ['red', 'free']:
                    is_inactive = True
                else:
                    is_color_on_table_inactive = True
                    for cb in self.color_ball_buttons:
                        if cb.property("color") == color:
                            is_color_on_table_inactive = cb.property("inactive")
                            break
                    is_inactive = is_color_on_table_inactive
            else:
                is_inactive = False

            ball_button.setProperty("inactive", is_inactive)
            ball_button.style().polish(ball_button)

    def calculate_score(self):
        """Calculates and updates the score display."""
        red_balls = self.red_balls_spinbox.value()
        player1_score = self.player1_score_spinbox.value()
        player2_score = self.player2_score_spinbox.value()

        remaining_points = red_balls * (BALL_COLORS["red"] + BALL_COLORS["black"])
        for ball_button in self.color_ball_buttons:
            if not ball_button.property("inactive"):
                remaining_points += int(ball_button.property("value"))

        difference = abs(player1_score - player2_score)

        message = ''
        if remaining_points == 0:
            if difference == 0:
                message = 'It’s a draw!'
            else:
                leading_player_text = 'Player 1' if player1_score > player2_score else 'Player 2'
                message = f"Frame is over! {leading_player_text} wins! Difference: {difference}"
        else:
            message = f"Difference: {difference}, Remaining: {remaining_points}"
            leading_player_text = 'Player 1' if player1_score > player2_score else 'Player 2'

            if difference >= remaining_points and red_balls == 0:
                message += f"<br> {leading_player_text} has won the frame!"

        self.result_label.setText(message)
        self.update_ball_states()

    def _apply_styles(self, stylesheet_name: str):
        """Loads and applies the stylesheet."""
        base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        stylesheet_path = os.path.join(base_path, stylesheet_name)

        try:
            with open(stylesheet_path, "r", encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            QMessageBox.warning(self, "Error", f"The stylesheet file '{stylesheet_path}' was not found.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error loading stylesheet: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SnookerScorerApp()
    window.show()
    sys.exit(app.exec())
