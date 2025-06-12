import sys
import random
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QListWidget, QMessageBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QTextEdit, QFormLayout,
    QSpinBox, QHeaderView
)
from tournament import Tournament

class SetupTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.players = []
        layout = QVBoxLayout(self)
        row = QHBoxLayout()
        self.entry = QLineEdit()
        self.entry.setPlaceholderText("Enter player name")
        self.entry.returnPressed.connect(self.add_player)
        row.addWidget(self.entry)
        for label, slot in (
            ("Add", self.add_player),
            ("Remove", self.remove_selected),
            ("Start", self.parent.start_tournament),
        ):
            btn = QPushButton(label)
            btn.clicked.connect(slot)
            row.addWidget(btn)
        layout.addLayout(row)
        self.listbox = QListWidget()
        layout.addWidget(self.listbox)

    def add_player(self):
        name = self.entry.text().strip()
        if name and name not in self.players:
            self.players.append(name)
            self.listbox.addItem(name)
        self.entry.clear()

    def remove_selected(self):
        for item in self.listbox.selectedItems():
            self.players.remove(item.text())
            self.listbox.takeItem(self.listbox.row(item))


class TournamentTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.pair_spins = []
        layout = QVBoxLayout(self)

        btns = QHBoxLayout()
        prev_btn = QPushButton("Previous Round"); prev_btn.clicked.connect(parent.show_previous_round)
        next_btn = QPushButton("Next Round");     next_btn.clicked.connect(parent.show_next_round)
        btns.addWidget(prev_btn); btns.addWidget(next_btn)
        layout.addLayout(btns)

        self.round_display = QTextEdit(readOnly=True, minimumHeight=120)
        layout.addWidget(self.round_display)

        self.form = QFormLayout()
        layout.addLayout(self.form)

        submit = QPushButton("Submit Scores"); submit.clicked.connect(parent.submit_current_scores)
        layout.addWidget(submit)
        layout.addStretch()

    def clear(self):
        self.round_display.clear()
        while self.form.count():
            w = self.form.takeAt(0).widget()
            if w: w.deleteLater()
        self.pair_spins.clear()

    def display_round(self, pairs, round_num, scores):
        self.clear()
        text = f"--- Round {round_num} ---\n"
        for idx, (p1, p2) in enumerate(pairs, start=1):
            text += f"Team {idx}: {p1.name} & {p2.name}\n"
            spin = QSpinBox(); spin.setRange(0,100); spin.setValue(scores[idx-1])
            self.form.addRow(f"{p1.name} & {p2.name}:", spin)
            self.pair_spins.append(((p1, p2), spin))
        self.round_display.setText(text)


class HistoryTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        layout = QHBoxLayout(self)

        self.list_widget = QListWidget()
        self.list_widget.itemSelectionChanged.connect(self.load_round)
        layout.addWidget(self.list_widget, 1)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Team", "Players", "Score"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 3)

        controls = QVBoxLayout()
        refresh = QPushButton("Refresh"); refresh.clicked.connect(self.update_list)
        save    = QPushButton("Save Changes"); save.clicked.connect(self.save_edits)
        controls.addWidget(refresh); controls.addWidget(save); controls.addStretch()
        layout.addLayout(controls)

        self.rounds = []  # list of (pairs, scores)

    def update_list(self):
        if not self.parent.tournament:
            return
        history, scores = self.parent.tournament.get_round_history()
        # pairs already (Player,Player)
        self.rounds = [(pairs, list(scores[idx])) for idx, (pairs, _) in enumerate(history)]
        self.list_widget.clear()
        for i in range(len(self.rounds)):
            self.list_widget.addItem(f"Round {i+1}")

    def load_round(self):
        idx = self.list_widget.currentRow()
        if idx < 0:
            return
        pairs, scrs = self.rounds[idx]
        self.table.setRowCount(len(pairs))
        for row, (p1, p2) in enumerate(pairs):
            team = f"Team {row+1}"
            players = f"{p1.name} & {p2.name}"
            self.table.setItem(row, 0, QTableWidgetItem(team))
            self.table.setItem(row, 1, QTableWidgetItem(players))
            item = QTableWidgetItem(str(scrs[row]))
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.table.setItem(row, 2, item)

    def save_edits(self):
        idx = self.list_widget.currentRow()
        if idx < 0:
            QMessageBox.warning(self, "No Round", "Select a round first.")
            return
        pairs, _ = self.rounds[idx]
        new_scores = []
        for row in range(self.table.rowCount()):
            try:
                new_scores.append(int(self.table.item(row, 2).text()))
            except:
                QMessageBox.critical(self, "Invalid", "Scores must be integers.")
                return
        # update local copy
        self.rounds[idx] = (pairs, new_scores)

        # overwrite tournament scores
        history, scores = self.parent.tournament.get_round_history()
        scores[idx] = new_scores

        # clear all players’ score lists and replay
        for p in self.parent.tournament.players:
            p.score.clear()
        for game_idx, (rnd_pairs, rnd_scores) in enumerate(zip(history, scores), start=1):
            for pair, pts in zip(rnd_pairs[0], rnd_scores):
                self.parent.tournament.record_result(game_idx, pair, pts)

        QMessageBox.information(self, "Saved", "Scores updated.")
        self.parent.leaderboard_tab.update_board()


class LeaderboardTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Player", "Total", "Games Played"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.update_board)
        layout.addWidget(refresh)

    def update_board(self):
        if not self.parent.tournament:
            return

        standings = sorted(
            self.parent.tournament.players,
            key=lambda p: sum(p.score),
            reverse=True
        )

        self.table.setRowCount(len(standings))
        for row, p in enumerate(standings):
            total = sum(p.score)
            games = len(p.score)

            for col, text in enumerate((p.name, str(total), str(games))):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)


class EuchreGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Euchre Tournament")
        self.tournament = None
        self.full_schedule = []
        self.displayed_round = 0

        self.tabs = QTabWidget()
        self.setup_tab      = SetupTab(self)
        self.tournament_tab = TournamentTab(self)
        self.history_tab    = HistoryTab(self)
        self.leaderboard_tab= LeaderboardTab(self)

        for w,t in ((self.setup_tab,"Setup"),
                    (self.tournament_tab,"Tournament"),
                    (self.history_tab,"History"),
                    (self.leaderboard_tab,"Leaderboard")):
            self.tabs.addTab(w,t)

        self.setCentralWidget(self.tabs)
        self.resize(800,600)

    def start_tournament(self):
        names = self.setup_tab.players
        if len(names)<4:
            return QMessageBox.critical(self,"Error","At least 4 players required.")

        self.tournament = Tournament(names)
        self.tournament.generate_full_schedule()
        random.shuffle(self.tournament.rounds)
        self.tournament.current_round = 0
        self.full_schedule = [pairs for pairs,_ in self.tournament.rounds]

        # reset all per-round scores to zero
        self.tournament.scores = [[0]*len(pairs) for pairs in self.full_schedule]

        self.displayed_round = 1
        self._render_round()

        self.history_tab.update_list()
        self.leaderboard_tab.update_board()

    def _render_round(self):
        # ensure tournament.current_round matches
        self.tournament.current_round = self.displayed_round
        # get pairs and existing scores
        pairs, _ = self.full_schedule[self.displayed_round-1], None
        _, scores = self.tournament.get_round_history()
        scrs = scores[self.displayed_round-1]
        # display
        self.tabs.setCurrentWidget(self.tournament_tab)
        self.tournament_tab.display_round(pairs, self.displayed_round, scrs)

    def show_next_round(self):
        if not self.tournament or self.displayed_round>=len(self.full_schedule):
            return QMessageBox.information(self,"Done","No more rounds.")
        self.displayed_round +=1
        self._render_round()

    def show_previous_round(self):
        if not self.tournament or self.displayed_round<=1:
            return QMessageBox.information(self,"First Round","Already at first round.")
        self.displayed_round -=1
        self._render_round()

    def submit_current_scores(self):
        if not self.tournament: return
        self.tournament.current_round = self.displayed_round
        for (p1,p2), spin in self.tournament_tab.pair_spins:
            self.tournament.record_result(self.displayed_round,(p1,p2),spin.value())

        self.history_tab.update_list()
        self.leaderboard_tab.update_board()
        self.show_next_round()

if __name__=="__main__":
    app = QApplication(sys.argv)
    gui = EuchreGUI()
    gui.show()
    sys.exit(app.exec())
