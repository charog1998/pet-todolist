import sys
import json
import os
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QLineEdit,
    QListWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QDateTimeEdit,
    QComboBox,
    QSystemTrayIcon,
    QMenu,
    QAction,
    QListWidgetItem,
    
)
from PyQt5.QtCore import Qt, QTimer, QDateTime, QSize, QPoint
from PyQt5.QtGui import QMovie, QIcon, QCursor, QFont, QPixmap


class TodoPetApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.initPet()
        self.initTray()
        self.loadTodos()
        self.checkDeadlineTimer = QTimer(self)
        self.checkDeadlineTimer.timeout.connect(self.checkDeadlines)
        self.checkDeadlineTimer.start(60000)  # 每分钟检查一次
        self.checkDeadlines()

    def initUI(self):
        # 主窗口设置
        self.setWindowTitle("待办清单")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon("pet_icon.png"))

        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # 左侧待办列表
        todo_frame = QFrame()
        todo_frame.setFrameShape(QFrame.StyledPanel)
        todo_frame.setMinimumWidth(500)
        todo_layout = QVBoxLayout(todo_frame)

        # 待办事项列表
        self.todo_list = QListWidget()
        self.todo_list.setStyleSheet(
            """
            QListWidget {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                border-bottom: 1px solid #eee;
                padding: 10px;
            }
            QListWidget::item:selected {
                background-color: #e0f7fa;
            }
        """
        )
        todo_layout.addWidget(self.todo_list)

        # 添加待办事项区域
        add_todo_layout = QVBoxLayout()

        # 任务输入
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("输入待办事项...")
        self.task_input.setStyleSheet(
            """
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
            }
        """
        )
        add_todo_layout.addWidget(self.task_input)

        # 时间和重复设置
        datetime_layout = QHBoxLayout()

        # 截止时间
        self.deadline_input = QDateTimeEdit()
        self.deadline_input.setDateTime(
            QDateTime.currentDateTime().addSecs(3600)
        )  # 默认1小时后
        self.deadline_input.setCalendarPopup(True)
        self.deadline_input.setStyleSheet(
            """
            QDateTimeEdit {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
            }
        """
        )
        datetime_layout.addWidget(QLabel("截止时间:"))
        datetime_layout.addWidget(self.deadline_input)

        # 重复次数
        self.repeat_combo = QComboBox()
        self.repeat_combo.addItems(["不重复", "每天", "每周", "每月"])
        self.repeat_combo.setStyleSheet(
            """
            QComboBox {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
            }
        """
        )
        datetime_layout.addWidget(QLabel("重复:"))
        datetime_layout.addWidget(self.repeat_combo)

        add_todo_layout.addLayout(datetime_layout)

        # 添加按钮
        self.add_button = QPushButton("添加待办事项")
        self.add_button.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """
        )
        self.add_button.clicked.connect(self.addTodo)
        add_todo_layout.addWidget(self.add_button)

        # 完成按钮
        self.complete_button = QPushButton("切换完成状态")
        self.complete_button.setStyleSheet(
            """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """
        )
        self.complete_button.clicked.connect(self.completeTodo)
        add_todo_layout.addWidget(self.complete_button)

        # 删除按钮
        self.delete_button = QPushButton("删除待办事项")
        self.delete_button.setStyleSheet(
            """
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """
        )
        self.delete_button.clicked.connect(self.deleteTodo)
        add_todo_layout.addWidget(self.delete_button)

        todo_layout.addLayout(add_todo_layout)

        # 右侧宠物信息区域
        pet_info_frame = QFrame()
        pet_info_frame.setFrameShape(QFrame.StyledPanel)
        pet_info_layout = QVBoxLayout(pet_info_frame)

        # 宠物状态信息
        self.pet_status = QLabel("状态: 😊")
        self.pet_status.setFont(QFont("Arial", 14))
        self.pet_status.setStyleSheet("color: #333; padding: 10px;")
        pet_info_layout.addWidget(self.pet_status)

        # 待办统计
        self.todo_stats = QLabel("待办事项统计: 0项待办")
        self.todo_stats.setFont(QFont("Arial", 12))
        self.todo_stats.setStyleSheet("color: #555; padding: 10px;")
        pet_info_layout.addWidget(self.todo_stats)

        # 紧急事项警告
        self.urgent_warning = QLabel("")
        self.urgent_warning.setFont(QFont("Arial", 12, QFont.Bold))
        self.urgent_warning.setStyleSheet("color: #d32f2f; padding: 10px;")
        pet_info_layout.addWidget(self.urgent_warning)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        pet_info_layout.addWidget(line)

        # 宠物行为说明
        instructions = QLabel(
            "说明:\n\n"
            "- 双击宠物可以显示/隐藏主窗口\n"
            "- 拖拽宠物可以移动位置\n"
            "- 宠物会根据待办事项状态改变表情\n"
            "- 右键宠物可以访问菜单"
        )
        instructions.setFont(QFont("Arial", 10))
        instructions.setStyleSheet("color: #666; padding: 10px;")
        instructions.setWordWrap(True)
        pet_info_layout.addWidget(instructions)

        # 添加到主布局
        main_layout.addWidget(todo_frame, 70)
        main_layout.addWidget(pet_info_frame, 30)

        # 初始化待办事项列表
        self.todos = []

    def initPet(self):
        # 创建宠物窗口
        self.pet_window = QWidget()
        self.pet_window.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow
        )
        self.pet_window.setAttribute(Qt.WA_TranslucentBackground)
        self.pet_window.setGeometry(100, 100, 150, 150)

        # 宠物标签
        self.pet_label = QLabel(self.pet_window)
        self.pet_label.setGeometry(0, 0, 150, 150)
        self.pet_label.setAlignment(Qt.AlignCenter)

        # 加载默认宠物动画
        self.loadPetAnimation("normal")

        # 显示宠物
        self.pet_window.show()

        # 鼠标事件用于拖动
        self.pet_window.mousePressEvent = self.petMousePress
        self.pet_window.mouseMoveEvent = self.petMouseMove
        self.pet_window.mouseDoubleClickEvent = self.toggleMainWindow

        # 右键菜单
        self.pet_window.setContextMenuPolicy(Qt.CustomContextMenu)
        self.pet_window.customContextMenuRequested.connect(self.showPetMenu)

    def loadPetAnimation(self, state):
        # 根据状态加载不同的动画
        if state == "normal":
            self.pet_movie = QMovie("normal_pet.gif")  # 正常状态
        elif state == "warning":
            self.pet_movie = QMovie("warning_pet.gif")  # 警告状态
        else:  # urgent
            self.pet_movie = QMovie("urgent_pet.gif")  # 紧急状态

        self.pet_label.setMovie(self.pet_movie)
        self.pet_movie.start()

    def petMousePress(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = (
                event.globalPos() - self.pet_window.frameGeometry().topLeft()
            )
            event.accept()

    def petMouseMove(self, event):
        if event.buttons() == Qt.LeftButton:
            self.pet_window.move(event.globalPos() - self.drag_position)
            event.accept()

    def toggleMainWindow(self, event):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.activateWindow()
            self.raise_()

    def showPetMenu(self, pos):
        menu = QMenu(self.pet_window)

        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.showMainWindow)
        menu.addAction(show_action)

        hide_action = QAction("隐藏主窗口", self)
        hide_action.triggered.connect(self.hide)
        menu.addAction(hide_action)

        menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.closeApp)
        menu.addAction(exit_action)

        menu.exec_(self.pet_window.mapToGlobal(pos))

    def showMainWindow(self):
        self.show()
        self.activateWindow()
        self.raise_()

    def initTray(self):
        # 创建系统托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("pet_icon.png"))

        # 创建托盘菜单
        tray_menu = QMenu()

        show_action = QAction("显示", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        hide_action = QAction("隐藏", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)

        tray_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.closeApp)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        # 托盘图标点击事件
        self.tray_icon.activated.connect(self.trayIconActivated)

    def trayIconActivated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()

    def addTodo(self):
        task = self.task_input.text().strip()
        if not task:
            return

        deadline = self.deadline_input.dateTime().toPyDateTime()
        repeat = self.repeat_combo.currentText()

        todo = {
            "id": len(self.todos) + 1,
            "task": task,
            "deadline": deadline.strftime("%Y-%m-%d %H:%M"),
            "repeat": repeat,
            "completed": False,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

        self.todos.append(todo)
        self.updateTodoList()
        self.task_input.clear()
        self.saveTodos()
        self.checkDeadlines()

    def completeTodo(self):
        selected = self.todo_list.currentRow()
        if selected >= 0 and selected < len(self.todos):
            self.todos[selected]["completed"] = not self.todos[selected]["completed"]
            self.updateTodoList()
            self.saveTodos()
            self.checkDeadlines()

    def deleteTodo(self):
        selected = self.todo_list.currentRow()
        if selected >= 0 and selected < len(self.todos):
            del self.todos[selected]
            self.updateTodoList()
            self.saveTodos()
            self.checkDeadlines()

    def updateTodoList(self):
        self.todo_list.clear()
        pending_count = 0

        self.todos = sorted(
            self.todos,
            key=lambda x: (x["completed"], x["deadline"]),  # 负号表示降序
        )

        for i, todo in enumerate(self.todos):
            # if todo["repeat"] == "不重复" and todo["completed"]:
            #     continue
            deadline = datetime.strptime(todo["deadline"], "%Y-%m-%d %H:%M")
            time_left = deadline - datetime.now()

            # 计算剩余时间描述
            if time_left.total_seconds() <= 0:
                time_str = "已超时!"
                color = "#d32f2f"
            elif time_left.days > 0:
                time_str = f"{time_left.days}天后"
                color = "#4CAF50"
            else:
                hours = time_left.seconds // 3600
                minutes = (time_left.seconds % 3600) // 60
                time_str = f"{hours}小时{minutes}分钟后"
                color = "#ff9800"

            # 创建列表项
            item_text = f"{todo['task']} - {deadline.strftime('%Y年%m月%d日 %H:%M')} ({time_str})"
            if todo["repeat"] != "不重复":
                item_text += f" [{todo['repeat']}]"

            # 创建自定义的widget作为列表项
            item_widget = QLabel(item_text)
            item_widget.setFont(QFont("Arial", 15, QFont.Bold))
            item_widget.setStyleSheet(f"color: {color}; padding: 10px;")

            if todo["completed"]:
                item_widget.setStyleSheet(
                    "color: #9e9e9e; text-decoration: line-through; padding: 10px;"
                )
            else:
                pending_count += 1

            # 创建QListWidgetItem并设置大小
            list_item = QListWidgetItem()
            list_item.setSizeHint(QSize(0, 100))
            
            # 添加到列表并设置widget
            self.todo_list.addItem(list_item)
            self.todo_list.setItemWidget(list_item, item_widget)

        # 更新统计信息
        self.todo_stats.setText(f"待办事项统计: {pending_count}项待办")

    def checkDeadlines(self):
        now = datetime.now()
        urgent_count = 0
        warning_count = 0

        for todo in self.todos:
            deadline = datetime.strptime(todo["deadline"], "%Y-%m-%d %H:%M")
            if todo["repeat"] == "每天":
                tmp_ddl = datetime(
                    now.year, now.month, now.day, deadline.hour, deadline.minute
                )
                # 先设成今天，然后检查具体时间是安排到今天还是明天
                if tmp_ddl < now:
                    tmp_ddl = tmp_ddl + timedelta(days=1) # 向后偏移1天
                deadline = tmp_ddl
                todo["deadline"] = deadline.strftime("%Y-%m-%d %H:%M")
                todo["completed"] = False

            if todo["repeat"] == "每周":
                tmp_ddl = datetime(
                    deadline.year, deadline.month, deadline.day, deadline.hour, deadline.minute
                )
                while tmp_ddl < now:
                    tmp_ddl = tmp_ddl + timedelta(weeks=1) # 向后偏移1周
                deadline = tmp_ddl
                todo["deadline"] = deadline.strftime("%Y-%m-%d %H:%M")
                todo["completed"] = False

            if todo["repeat"] == "每月":
                tmp_ddl = datetime(
                    deadline.year, deadline.month, deadline.day, deadline.hour, deadline.minute
                )
                while tmp_ddl < now:
                    new_month = tmp_ddl.month + 1
                    if new_month > 12:
                        new_month = 1
                        new_year = tmp_ddl.year + 1
                    else:
                        new_year = tmp_ddl.year
                    tmp_ddl = tmp_ddl.replace(year=new_year, month=new_month)
                deadline = tmp_ddl
                todo["deadline"] = deadline.strftime("%Y-%m-%d %H:%M")
                todo["completed"] = False

            if todo["completed"]:
                continue

            time_left = deadline - now

            # 检查紧急程度
            if time_left.total_seconds() <= 0:
                urgent_count += 1
            elif time_left.total_seconds() <= 3600:  # 1小时内
                urgent_count += 1
            elif time_left.total_seconds() <= 43200:  # 12小时内
                warning_count += 1

        # 更新宠物状态
        if urgent_count > 0:
            self.pet_status.setText("状态: 😱")
            self.urgent_warning.setText(
                f"警告: 有{urgent_count}个待办事项即将超期或已超期!"
            )
            self.loadPetAnimation("urgent")
        elif warning_count > 0:
            self.pet_status.setText("状态: 😟")
            self.urgent_warning.setText(
                f"提示: 有{warning_count}个待办事项将在12小时内到期"
            )
            self.loadPetAnimation("warning")
        else:
            self.pet_status.setText("状态: 😊")
            self.urgent_warning.setText("")
            self.loadPetAnimation("normal")

        # 更新待办列表
        self.updateTodoList()

    def saveTodos(self):
        with open("todos.json", "w") as f:
            json.dump(self.todos, f, indent=2)

    def loadTodos(self):
        try:
            if os.path.exists("todos.json"):
                with open("todos.json", "r") as f:
                    self.todos = json.load(f)
                self.updateTodoList()
        except:
            self.todos = []

    def closeApp(self):
        self.saveTodos()
        self.pet_window.close()
        QApplication.quit()

    def closeEvent(self, event):
        # 隐藏而不是关闭，保持宠物可见
        event.ignore()
        self.hide()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 设置应用程序样式
    app.setStyle("Fusion")

    # 创建并显示主窗口
    window = TodoPetApp()
    window.show()

    sys.exit(app.exec_())
