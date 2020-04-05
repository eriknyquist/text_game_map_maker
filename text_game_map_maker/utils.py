from PyQt5 import QtWidgets


def yesNoDialog(parent, header="", msg="Are you sure?"):
    reply = QtWidgets.QMessageBox.question(parent, header, msg,
                                           (QtWidgets.QMessageBox.Yes |
                                           QtWidgets.QMessageBox.No |
                                           QtWidgets.QMessageBox.Cancel),
                                           QtWidgets.QMessageBox.Cancel)

    return reply == QtWidgets.QMessageBox.Yes

def errorDialog(parent, heading="Error", message="Unrecoverable error occurred"):
    msg = QtWidgets.QMessageBox(parent)
    msg.setIcon(QtWidgets.QMessageBox.Critical)
    msg.setText(heading)
    msg.setInformativeText(message)
    msg.setWindowTitle("Critical error!")
    msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
    msg.exec_()

def infoDialog(parent, heading="", message=""):
    msg = QtWidgets.QMessageBox(parent)
    msg.setIcon(QtWidgets.QMessageBox.Information)
    msg.setText(heading)
    msg.setInformativeText(message)
    msg.setWindowTitle("Information")
    msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
    msg.exec_()

