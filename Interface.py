import json
import re
import csv
import logging
import requests
import boto3
import pandas as pd
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QStackedLayout, QTextEdit, QTabWidget, QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox, QLineEdit
from PyQt5.QtGui import QPixmap, QFont, QIcon
from PyQt5.QtCore import Qt, pyqtSignal, QSize
import paho.mqtt.client as mqtt
from botocore.exceptions import ClientError
from datetime import datetime


class MyWindow(QWidget):
    update_position = pyqtSignal(str)
    update_battery = pyqtSignal(str)
    update_status = pyqtSignal(str)
    update_table = pyqtSignal(list)
    update_ip = pyqtSignal(list)
    update_camara = pyqtSignal(list)
    update_ui = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.ej1 = 0
        self.ej2 = 0
        self.client = None
        self.default_ip = self.load_default_ip()
        self.setGeometry(0, 0, 1366, 1000)
        self.setWindowTitle("San Francisco Farmers Market Interface")
        self.pixmap = QPixmap("C:/Users/Alan/Downloads/Prueba/Prueba/img/back.jpeg")
        self.mainLayout()
        # self.initMQTT()

    # ---- LAYOUTS -----------------------------------------------------------------------------------------

    def mainLayout(self):
        layout = QVBoxLayout()

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.image_label = QLabel(self)
        pixmap = QPixmap("C:/Users/Alan/Downloads/Prueba/Prueba/img/head.png")
        self.image_label.setPixmap(pixmap)
        self.image_label.setAlignment(Qt.AlignTop)
        layout.addWidget(self.image_label)

        self.mainlabel = QLabel("San Francisco Farmers Market Interface")
        font = QFont("Times New Roman", 25, QFont.Bold)
        self.mainlabel.setFont(font)
        self.mainlabel.setAlignment(Qt.AlignJustify)
        layout.addWidget(self.mainlabel)
        layout.addSpacing(50)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabBar::tab {
                font-size: 25px;  /* Tamaño de la fuente */
                height: 50px;     /* Altura de la pestaña */
                width: 200px;     /* Anchura de la pestaña */
            }
        """)
        layout.addWidget(self.tabs)

        # Pestaña de carga de audio
        self.inicio_tab = QWidget()
        self.inicio_tabLayout()
        self.tabs.addTab(self.inicio_tab, "Home")

        # Pestaña de Transformada de Fourier
        self.history_tab = QWidget()
        self.history_tabLayout()
        self.tabs.addTab(self.history_tab, "History")

        self.mant_tab = QWidget()
        self.mant_tabLayout()
        self.tabs.addTab(self.mant_tab, "Maintenance")

        self.setLayout(layout)

    def inicio_tabLayout(self):
        layout = QVBoxLayout()

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.mainlabel_home = QLabel("Robot's State")
        font = QFont("Times New Roman", 25, QFont.Bold)
        self.mainlabel_home.setFont(font)
        layout.addWidget(self.mainlabel_home, alignment=Qt.AlignTop)
        layout.addSpacing(150)

        ip_layout = QHBoxLayout()
        ip_layout.setAlignment(Qt.AlignLeft)

        self.ip = QPushButton()
        icon_ip = QIcon("C:/Users/Alan/Downloads/Prueba/Prueba/img/ip.png")
        self.ip.setIcon(icon_ip)
        self.ip.setIconSize(QSize(80, 80))
        self.ip.setFixedSize(400, 100)
        self.ip.setText(f"IP: {self.default_ip}")
        self.ip.setStyleSheet("""
            background-color: #e5e5e5; 
            color: black; 
            border-radius: 5px; 
            font-size: 25px;  /* Aquí se especifica el tamaño de la fuente */
            font-weight: bold;  /* Opcional: para hacer la fuente en negrita */
        """)
        ip_layout.addWidget(self.ip)

        self.start_mqtt_button = QPushButton("Start Connection", self)
        self.start_mqtt_button.setGeometry(150, 130, 100, 30)
        self.start_mqtt_button.setStyleSheet("""
            QPushButton {
                background-color: #e5e5e5; 
                color: black; 
                border-radius: 5px; 
                font-size: 25px;  /* Aquí se especifica el tamaño de la fuente */
                font-weight: bold;  /* Opcional: para hacer la fuente en negrita */
            }
            QPushButton:hover {
                background-color: #d4d4d4;  /* Color al pasar el ratón por encima */
            }
            QPushButton:pressed {
                background-color: #bcbcbc;  /* Color al hacer clic */
            }
        """)
        self.start_mqtt_button.clicked.connect(self.initMQTT)
        ip_layout.addWidget(self.start_mqtt_button)

        self.ip_input = QLineEdit(self)
        self.ip_input.setText(self.default_ip)
        self.ip_input.setStyleSheet("font-size: 25px;")
        self.ip_input.textChanged.connect(self.validate_ip)
        ip_layout.addWidget(self.ip_input)

        self.ip_status = QLabel()
        self.ip_status.setStyleSheet("font-size: 25px;")
        self.ip_status.setVisible(False)
        ip_layout.addWidget(self.ip_status)

        self.save_default_ip = QPushButton("Save as default IP", self)
        self.save_default_ip.setGeometry(150, 130, 100, 30)
        self.save_default_ip.setStyleSheet("""
            QPushButton {
                background-color: #e5e5e5; 
                color: black; 
                border-radius: 5px; 
                font-size: 25px;  /* Aquí se especifica el tamaño de la fuente */
                font-weight: bold;  /* Opcional: para hacer la fuente en negrita */
            }
            QPushButton:hover {
                background-color: #d4d4d4;  /* Color al pasar el ratón por encima */
            }
            QPushButton:pressed {
                background-color: #bcbcbc;  /* Color al hacer clic */
            }
        """)
        self.save_default_ip.clicked.connect(self.Save_ip)
        ip_layout.addWidget(self.save_default_ip)

        layout.addLayout(ip_layout)

        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignCenter)

        self.position = QPushButton()
        icon_pos = QIcon("C:/Users/Alan/Downloads/Prueba/Prueba/img/location.png")
        self.position.setIcon(icon_pos)
        self.position.setIconSize(QSize(90, 90))
        self.position.setFixedSize(400, 150)
        self.position.setText("Aisle:\nRack:")
        self.position.setStyleSheet("""
            background-color: #f53a3a; 
            color: white; 
            border-radius: 15px; 
            font-size: 25px;  /* Aquí se especifica el tamaño de la fuente */
            font-weight: bold;  /* Opcional: para hacer la fuente en negrita */
        """)
        button_layout.addWidget(self.position)

        self.battery = QPushButton()
        icon_bat = QIcon("C:/Users/Alan/Downloads/Prueba/Prueba/img/bateria.png")
        self.battery.setIcon(icon_bat)
        self.battery.setIconSize(QSize(90, 90))
        self.battery.setFixedSize(500, 150)
        self.battery.setText("Battery Wheels: \nBattery System: ")
        self.battery.setStyleSheet("""
            background-color: #0cc0df; 
            color: white; 
            border-radius: 15px; 
            font-size: 25px;  /* Aquí se especifica el tamaño de la fuente */
            font-weight: bold;  /* Opcional: para hacer la fuente en negrita */
        """)
        button_layout.addWidget(self.battery)

        self.work = QPushButton()
        icon_work = QIcon("C:/Users/Alan/Downloads/Prueba/Prueba/img/work.png")
        self.work.setIcon(icon_work)
        self.work.setIconSize(QSize(90, 90))
        self.work.setFixedSize(300, 150)
        self.work.setText("Status: Off")
        self.work.setStyleSheet("""
            background-color: #00bf63; 
            color: white; 
            border-radius: 15px; 
            font-size: 25px;  /* Aquí se especifica el tamaño de la fuente */
            font-weight: bold;  /* Opcional: para hacer la fuente en negrita */
        """)
        button_layout.addWidget(self.work)

        layout.addLayout(button_layout)
        layout.setAlignment(Qt.AlignCenter)

        download = QPushButton()
        icon_down = QIcon("C:/Users/Alan/Downloads/Prueba/Prueba/img/download.png")
        download.setIcon(icon_down)
        download.setIconSize(QSize(80, 80))
        download.setFixedHeight(150)
        download.setText("Download Inventory")
        download.setStyleSheet("""
            background-color: #cb6ce6; 
            color: white; 
            border-radius: 15px; 
            font-size: 25px;  /* Aquí se especifica el tamaño de la fuente */
            font-weight: bold;  /* Opcional: para hacer la fuente en negrita */
        """)

        self.download_label = QLabel()
        self.download_label.setVisible(False)
        layout.addWidget(download)
        layout.addWidget(self.download_label)

        self.update_ip.connect(self.ip.setText)
        self.update_position.connect(self.position.setText)
        self.update_battery.connect(self.battery.setText)
        self.update_status.connect(self.work.setText)
        download.clicked.connect(self.download_file)

        self.inicio_tab.setLayout(layout)

    def history_tabLayout(self):
        layout = QVBoxLayout()

        self.mainlabel_home = QLabel("Robot Position History")
        font = QFont("Times New Roman", 25, QFont.Bold)
        self.mainlabel_home.setFont(font)
        layout.addWidget(self.mainlabel_home, alignment=Qt.AlignTop)

        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignLeft)

        self.hist = QPushButton()
        icon_history = QIcon("C:/Users/Alan/Downloads/Prueba/Prueba/img/history.png")
        self.hist.setIcon(icon_history)
        self.hist.setIconSize(QSize(50, 50))
        self.hist.setText("Update")
        self.hist.setFixedSize(250, 80)
        self.hist.setStyleSheet("""
            background-color: #ff8311; 
            color: black; 
            border-radius: 15px; 
            font-size: 25px;  /* Aquí se especifica el tamaño de la fuente */
            font-weight: bold;  /* Opcional: para hacer la fuente en negrita */
        """)
        self.hist.clicked.connect(self.load_data_into_table)
        button_layout.addWidget(self.hist)

        self.downl = QPushButton()
        icon_downl = QIcon("C:/Users/Alan/Downloads/Prueba/Prueba/img/download.png")
        self.downl.setIcon(icon_downl)
        self.downl.setIconSize(QSize(50, 50))
        self.downl.setText("Download")
        self.downl.setFixedSize(250, 80)
        self.downl.setStyleSheet("""
            background-color: #ff8311; 
            color: black; 
            border-radius: 15px; 
            font-size: 25px;  /* Aquí se especifica el tamaño de la fuente */
            font-weight: bold;  /* Opcional: para hacer la fuente en negrita */
        """)
        self.downl.clicked.connect(self.export_table_to_excel)
        button_layout.addWidget(self.downl)

        layout.addLayout(button_layout)
        layout.setAlignment(Qt.AlignCenter)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["Date", "Position", "Battery", "Status"])
        self.history_table.setStyleSheet("""
            QHeaderView::section {
                font-size: 16px;  /* Tamaño de la fuente de los encabezados */
                height: 40px;     /* Altura de los encabezados */
            }
            QTableWidget {
                font-size: 14px;  /* Tamaño de la fuente de los datos */
            }
            QTableWidget::item {
                height: 30px;     /* Altura de las filas */
            }
        """)
        layout.addWidget(self.history_table)

        self.history_tab.setLayout(layout)

        self.history_table.resizeRowsToContents()
        self.history_table.setColumnWidth(0, 350)
        self.history_table.setColumnWidth(1, 300)
        self.history_table.setColumnWidth(2, 500)
        self.history_table.setColumnWidth(3, 150)
        for row in range(self.history_table.rowCount()):
            self.history_table.setRowHeight(row, 130)

    def mant_tabLayout(self):
        layout = QVBoxLayout()

        self.mainlabel_home = QLabel("Battery Levels")
        font = QFont("Times New Roman", 25, QFont.Bold)
        self.mainlabel_home.setFont(font)
        layout.addWidget(self.mainlabel_home, alignment=Qt.AlignTop)

        self.maint = QPushButton()
        self.maint2 = QPushButton()
        self.camera = QPushButton()

        if self.ej1 == 0:
            icon_maintenance = QIcon("C:/Users/Alan/Downloads/Prueba/Prueba/img/full.png")
            self.maint.setIcon(icon_maintenance)
            self.maint.setIconSize(QSize(120, 120))
            self.maint.setText("Battery level Wheels: Good")
            
            self.maint.setFixedHeight(150)

        if self.ej2 == 0:
            icon_maintenance = QIcon("C:/Users/Alan/Downloads/Prueba/Prueba/img/full.png")
            self.maint2.setIcon(icon_maintenance)
            self.maint2.setIconSize(QSize(120, 120))
            self.maint2.setText("Battery level System: Good")
            self.maint2.setFixedHeight(150)

        self.maint.setStyleSheet("background-color : #eeeeee; border-radius: 5px; font-size: 20px; font-weight: bold")
        self.maint2.setStyleSheet("background-color : #eeeeee; border-radius: 5px; font-size: 20px; font-weight: bold")
        self.camera.setStyleSheet("background-color : #eeeeee; border-radius: 5px; font-size: 20px; font-weight: bold")

        self.label = QLabel("Camera Status")
        font = QFont("Times New Roman", 25, QFont.Bold)
        self.label.setFont(font)

        icon_cam = QIcon("C:/Users/Alan/Downloads/Prueba/Prueba/img/cam.png")
        self.camera.setIcon(icon_cam)
        self.camera.setIconSize(QSize(120, 120))
        self.camera.setText("Camera Maintenance: None")
        self.camera.setFixedHeight(150)

        self.update_camara.connect(self.camera.setText)

        layout.addWidget(self.maint, alignment=Qt.AlignTop)
        layout.addWidget(self.maint2, alignment=Qt.AlignTop)
        layout.addWidget(self.label, alignment=Qt.AlignTop)
        layout.addWidget(self.camera, alignment=Qt.AlignTop)

        self.mant_tab.setLayout(layout)

    # ---- MQTT --------------------------------------------------------------------------------------------

    def clear(self):
        self.history_table.clearContents()
        self.history_table.setRowCount(0)

    def export_table_to_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Guardar archivo", "", "CSV(*.csv)")
        if path:
            with open(path, 'w', newline='') as file:
                writer = csv.writer(file)
                header = [self.history_table.horizontalHeaderItem(i).text() for i in range(self.history_table.columnCount())]
                writer.writerow(header)
                for row in range(self.history_table.rowCount()):
                    row_data = []
                    for column in range(self.history_table.columnCount()):
                        item = self.history_table.item(row, column)
                        row_data.append(item.text() if item is not None else '')
                    writer.writerow(row_data)

    def export_table_to_excel(self):
        data = []
        for row in range(self.history_table.rowCount()):
            row_data = []
            for column in range(self.history_table.columnCount()):
                item = self.history_table.item(row, column)
                row_data.append(item.text() if item is not None else '')
            data.append(row_data)

        df = pd.DataFrame(data, columns=[self.history_table.horizontalHeaderItem(i).text() for i in range(self.history_table.columnCount())])

        path, _ = QFileDialog.getSaveFileName(self, "Guardar archivo", "", "Excel Files (*.xlsx)")
        if path:
            if not path.endswith('.xlsx'):
                path += '.xlsx'
            try:
                df.to_excel(path, index=False)
            except Exception as e:
                print(f"Failed to write to Excel: {e}")
                QMessageBox.critical(self, "Error de Exportación", "No se pudo exportar a Excel.")
        else:
            QMessageBox.information(self, "Operación Cancelada", "No se ha seleccionado ningún archivo para guardar.")

    def maintenance(self):
        pass

    # ---- MQTT --------------------------------------------------------------------------------------------

    def initMQTT(self):
        try:
            self.ip_status.setVisible(True)
            self.ip_status.setStyleSheet("color: orange;")
            self.ip_status.setText("connecting")
            QApplication.processEvents()

            ip = self.ip_input.text()
            if ip is None:
                ip = "192.168.1.121"

            if self.client is not None:
                self.client.loop_stop()
                self.client.disconnect()

            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message

            # Set MQTT username and password
            self.client.username_pw_set("user1", "1234")

            self.client.connect(ip, 1883, 60)  # Ensure correct MQTT broker address and port
            self.client.loop_start()
            self.ip.setText("IP: " + str(ip))
            self.ip_status.setStyleSheet("color: green;")
            self.ip_status.setText("connection success")
        except Exception as e:
            self.ip_status.setStyleSheet("color: red;")
            self.ip_status.setText("connection failed")
            self.show_alert(str(e))


    def show_alert(self, message):
        self.alert = QMessageBox()
        self.alert.setWindowTitle("Error de Conexión")
        self.alert.setText(f"No se pudo conectar al broker MQTT.\nError: {message}")
        self.alert.setIcon(QMessageBox.Warning)
        self.alert.setStandardButtons(QMessageBox.Retry | QMessageBox.Cancel)
        self.alert.buttonClicked.connect(self.handle_alert_button)
        self.start_mqtt_button.setVisible(True)  # Mostrar el botón de reintentar
        self.alert.exec_()

    def handle_alert_button(self, button):
        print(button.text())
        if button.text() == "Retry":
            self.alert.close()
            self.initMQTT()
        else:
            self.alert.close()

    def closeEvent(self, event):
        print("Entro a close Event")
        if self.client is not None:
            self.client.loop_stop()
            self.client.disconnect()
        event.accept()

    def on_connect(self, client, userdata, flags, rc, properties=None):
        print("Connected with result code " + str(rc))
        client.subscribe("test/topic")

    def on_message(self, client, userdata, msg):
        message = msg.payload.decode('utf-8')
        print("Received message:", message)

        if "Aisle" in message:
            parts = message.split(',')
            data = {part.split(':')[0].strip(): part.split(':')[1].strip() for part in parts}

            position = f"Aisle: {data['Aisle']},\nRack: {data['Rack']}"
            battery = f"Battery Wheels: {data['Battery Wheels']},\nBattery System: {data['Battery System']}"
            status = f"Status: {data['Status']}"

            if data['Battery Wheels'] == "Charged":
                self.set_charged_battery("Wheels")
            else:
                self.set_critical_battery("Wheels")

            if data['Battery System'] == "Charged":
                self.set_charged_battery("System")
            else:
                self.set_critical_battery("System")

            self.update_position.emit(position)
            self.update_battery.emit(battery)
            self.update_status.emit(status)

            full_data = {
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Position": position,
                "Battery": battery,
                "Status": status
            }
            self.write_json(full_data)
            self.update_ui.emit()

        elif "Camera" in message:
            cam_info = message.split(':')[1].strip()
            self.camera.setText(f"Camera Maintenance: {str(cam_info)}")


    def validate_ip(self):
        ip = self.ip_input.text()
        if self.is_valid_ip(ip):
            self.ip.setText(f'IP: ready to connect')
            self.save_default_ip.setEnabled(True)
        else:
            self.ip.setText('IP actual: invalid IP')
            self.save_default_ip.setEnabled(False)

    def is_valid_ip(self, ip):
        ip_regex = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
        if not ip_regex.match(ip):
            return False

        parts = ip.split('.')
        for part in parts:
            if int(part) > 255:
                return False

        return True

    def Save_ip(self):
        ip = self.ip_input.text()
        if self.is_valid_ip(ip):
            try:
                with open('robot_data.json', 'r') as file:
                    existing_data = json.load(file)
                    if not isinstance(existing_data, list):
                        existing_data = []
            except (FileNotFoundError, json.JSONDecodeError):
                existing_data = []

            # Remove any existing IP entries
            existing_data = [entry for entry in existing_data if "IP" not in entry]

            # Add the new IP entry
            ip_data = {"IP": ip}
            existing_data.append(ip_data)

            with open('robot_data.json', 'w') as file:
                json.dump(existing_data, file)
            QMessageBox.information(self, "Success", "IP saved successfully")
        else:
            QMessageBox.warning(self, "Invalid IP", "The IP address is not valid")


    def write_json(self, data):
        try:
            with open('robot_data.json', 'r') as file:
                existing_data = json.load(file)
                if not isinstance(existing_data, list):
                    existing_data = []
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = []

        existing_data.append(data)

        if len(existing_data) > 50:
            existing_data = existing_data[-50:]

        with open('robot_data.json', 'w') as file:
            json.dump(existing_data, file)

    def load_data_into_table(self):
        try:
            with open('robot_data.json', 'r') as file:
                data = json.load(file)

            self.history_table.setRowCount(len(data))
            for row_index, entry in enumerate(data):
                if "Date" in entry and "Position" in entry and "Battery" in entry and "Status" in entry:
                    self.history_table.setItem(row_index, 0, QTableWidgetItem(entry['Date']))
                    self.history_table.setItem(row_index, 1, QTableWidgetItem(entry['Position']))
                    self.history_table.setItem(row_index, 2, QTableWidgetItem(entry['Battery']))
                    self.history_table.setItem(row_index, 3, QTableWidgetItem(entry['Status']))
                else:
                    self.history_table.setItem(row_index, 0, QTableWidgetItem(""))
                    self.history_table.setItem(row_index, 1, QTableWidgetItem(""))
                    self.history_table.setItem(row_index, 2, QTableWidgetItem(""))
                    self.history_table.setItem(row_index, 3, QTableWidgetItem(""))

            self.history_table.resizeRowsToContents()

        except Exception as e:
            print("Failed to load or parse the JSON data:", e)

    def set_critical_battery(self, arg):
        icon_maintenance = QIcon("C:/Users/Alan/Downloads/Prueba/Prueba/img/low.png")
        print(arg, "Critical")
        if arg == "Wheels":
            self.maint.setIcon(icon_maintenance)
            self.maint.setIconSize(QSize(120, 120))
            self.maint.setText("Battery Level Wheels: Critical")
        else:
            self.maint2.setIcon(icon_maintenance)
            self.maint2.setIconSize(QSize(120, 120))
            self.maint2.setText("Battery Level System: Critical")

    def set_charged_battery(self, arg):
        print(arg, "Good")
        icon_maintenance = QIcon("C:/Users/Alan/Downloads/Prueba/Prueba/img/full.png")
        if arg == "Wheels":
            self.maint.setIcon(icon_maintenance)
            self.maint.setIconSize(QSize(120, 120))
            self.maint.setText("Battery Level Wheels: Good")
        else:
            self.maint2.setIcon(icon_maintenance)
            self.maint2.setIconSize(QSize(120, 120))
            self.maint2.setText("Battery Level System: Good")

    # ---- AWS --------------------------------------------------------------------------------------------

    def download_file(self):
        self.downl.setEnabled(False)
        self.download_label.setVisible(True)
        self.download_label.setStyleSheet("color: orange;")
        self.download_label.setText("downloading")
        QApplication.processEvents()
        url = "https://n5vurzez1l.execute-api.us-east-2.amazonaws.com/default/csvlambda"
        mydict = {}
        headers = {"Content-Type": "application/json;charset=utf-8"}
        res = requests.post(url, json=mydict, headers=headers)

        #Add your AWS access and secret key
        s3_client = boto3.client(
            's3',
            aws_access_key_id='',
            aws_secret_access_key='',
        )

        try:
            response = s3_client.download_file('inventory-irs', 'inventory.csv', 'inventory.csv')
            print(open('inventory.csv').read())
            self.download_label.setStyleSheet("color: green;")
            self.download_label.setText("successfull download")
            self.downl.setEnabled(True)
        except ClientError as e:
            logging.error(e)
            self.download_label.setStyleSheet("color: red;")
            self.download_label.setText("unable to download")
            self.downl.setEnabled(True)
            return False
        return True

    def load_default_ip(self):
        try:
            with open('robot_data.json', 'r') as file:
                existing_data = json.load(file)
                for entry in existing_data:
                    if "IP" in entry:
                        print("ip default:",entry["IP"])
                        return entry["IP"]
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return "192.168.1.121"

def main():
    app = QApplication([])
    window = MyWindow()
    window.show()
    app.exec_()

if __name__ == '__main__':
    main()
