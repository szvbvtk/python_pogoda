from PyQt6.QtWidgets import QGridLayout, QPushButton, QLabel, QDialog
class ErrorDialog(QDialog):
    """
    Informacja o błędzie wyskakująca po wpisaniu nieprawidłowej nazwy miejscowości
    """
    def __init__(self):
        super().__init__()
        layout = QGridLayout()
        self.lbl = QLabel("Nie udało się odszukać podanej miejscowości :(")
        self.btn = QPushButton("Zamknij")
        self.setWindowTitle("Błąd")
        layout.addWidget(self.lbl, 0, 0, 1, 4)
        layout.addWidget(self.btn, 1, 1, 1, 2)
        self.btn.clicked.connect(self.accept)

        self.setLayout(layout)
