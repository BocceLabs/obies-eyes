# import packages, modules, classes, and functions
from PyQt5.QtWidgets import QApplication
from views.viewsui import MainWindow

# start application with windows for each camera
app = QApplication([])

# start windows
win = MainWindow()

# show windows
win.show()

# exit app when all windows are closed
app.exit(app.exec_())