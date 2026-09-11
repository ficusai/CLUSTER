from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGroupBox,
                               QPushButton, QTextEdit, QFrame, QSizePolicy,
                               QMessageBox)
from PySide6.QtGui import QFont


class DeployTab(QWidget):
    def __init__(self, bridge=None, parent=None):
        super().__init__(parent)
        self.bridge = bridge
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        self._title("Android Worker Deployment via Termux")
        self._desc("Connect an Android phone as a cluster worker node using Termux and SSH. Follow the steps below in order.")

        self._step("1 — Install Termux",
            "Download and install <b>Termux</b> from <a href='https://f-droid.org/en/packages/com.termux/'>F-Droid</a> "
            "(NOT Google Play, as the Play Store version is outdated). Open Termux and run:",
            [
                "pkg update && pkg upgrade -y",
                "termux-setup-storage",
            ],
            note="Grant storage permission when prompted.")

        self._step("2 — Install Dependencies in Termux",
            "Run these commands inside the Termux terminal on your Android device:",
            [
                "pkg install -y python git openssh",
                "pip install --upgrade pip pyyaml zeroconf psutil rich",
            ],
            note="This installs Python, Git, OpenSSH, and the cluster worker dependencies.")

        self._step("3 — Bootstrap the Cluster Worker",
            "Download and run the bootstrap script inside Termux. This sets up the SSH daemon and worker directory:",
            [
                "wget -O setup-termux.sh https://raw.githubusercontent.com/ficusai/CLUSTER/main/setup-termux.sh",
                "bash setup-termux.sh",
            ],
            note="The script starts sshd on port 8022 and creates ~/.termux/boot/ for auto-start on boot.")

        self._step("4 — Find Your Android IP Address",
            "In Termux, get the phone's local IP address. It will be needed for SSH from the host:",
            [
                "hostname -I",
            ],
            note="Note the IP address (e.g., 192.168.1.50). Make sure your host computer and phone are on the same WiFi network.")

        self._step("5 — Start the rpc-server on Android",
            "In Termux, start the worker. Replace <IP> with your root host's IP address:",
            [
                "mkdir -p ~/ai-cluster",
                "cd ~/ai-cluster",
                "./start-worker.sh",
            ],
            note="If the binary doesn't exist yet, the root coordinator will push it in the next step. "
                 "Alternatively, run: pkg install -y cmake clang make && "
                 "git clone https://github.com/ggml-org/llama.cpp.git && cd llama.cpp && "
                 "cmake -S . -B build -DGGML_RPC=ON && cmake --build build -j$(nproc) && "
                 "cp build/bin/rpc-server ~/ai-cluster/",
            subtitle="Manual build (if rpc-server binary is not available)",
            )

        self._step("6 — Connect from Host (Linux)",
            "From the host computer, SSH into the Android device to verify connectivity and deploy the worker binary if needed:",
            [
                "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "
                "-p 8022 u0_a377@<PHONE_IP>",
            ],
            note="Replace <PHONE_IP> with the IP from Step 4. If the default user doesn't work, "
                 "try 'termux' as the username. Use the SSH key from config.yaml's "
                 "<code>workers.deploy_credentials.android.key</code> with: <code>-i path/to/key</code>")

        self._step("7 — Set Up Auto-Start (Optional)",
            "To automatically start the worker on phone boot, install <b>Termux:Boot</b> from F-Droid and place the startup script:",
            [
                "mkdir -p ~/.termux/boot",
                "cat > ~/.termux/boot/start-worker.sh << 'EOF'",
                "#!/data/data/com.termux/files/usr/bin/bash",
                "sleep 10",
                "cd ~/ai-cluster",
                "exec ./start-worker.sh",
                "EOF",
                "chmod +x ~/.termux/boot/start-worker.sh",
            ],
            note="Requires the Termux:Boot app installed from F-Droid.")

        layout.addStretch()

    def _title(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 18px; font-weight: 700; color: #ffffff;")
        self.layout().addWidget(lbl)

    def _desc(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 13px; color: #9ca3af;")
        lbl.setWordWrap(True)
        self.layout().addWidget(lbl)

    def _step(self, title, desc, commands, note="", subtitle=""):
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                color: #e2e8f0;
                border: 1px solid #0f3460;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding-left: 8px;
                padding-top: 0px;
            }
        """)
        vlayout = QVBoxLayout(group)
        vlayout.setSpacing(6)

        # Description
        desc_lbl = QLabel(desc)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("font-size: 12px; color: #9ca3af;")
        vlayout.addWidget(desc_lbl)

        # Commands
        for cmd in commands:
            cmd_frame = QFrame()
            cmd_frame.setStyleSheet("background-color: #0f3460; border-radius: 4px;")
            cmd_layout = QHBoxLayout(cmd_frame)
            cmd_layout.setContentsMargins(8, 4, 8, 4)
            cmd_layout.setSpacing(8)

            cmd_lbl = QLabel(f"<code>{cmd}</code>")
            cmd_lbl.setStyleSheet("font-size: 12px; color: #4ade80; font-family: monospace;")
            cmd_lbl.setTextFormat(Qt.RichText)
            cmd_lbl.adjustSize()

            copy_btn = QPushButton("Copy")
            copy_btn.setMaximumWidth(50)
            copy_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1a4f8b;
                    color: #ffffff;
                    border: none;
                    border-radius: 3px;
                    font-size: 11px;
                    padding: 2px 6px;
                }
                QPushButton:hover { background-color: #2563a0; }
            """)
            copy_btn.clicked.connect(lambda checked, c=cmd: self._copy_cmd(c))
            cmd_layout.addWidget(cmd_lbl, stretch=1)
            cmd_layout.addWidget(copy_btn)
            vlayout.addWidget(cmd_frame)

        if subtitle:
            sub_lbl = QLabel(subtitle)
            sub_lbl.setStyleSheet("font-size: 11px; color: #fbbf24; font-weight: 600; margin-top: 4px;")
            vlayout.addWidget(sub_lbl)

        # Note
        if note:
            note_lbl = QLabel(f"<b>Note:</b> {note}")
            note_lbl.setWordWrap(True)
            note_lbl.setStyleSheet("font-size: 11px; color: #6b7280; margin-top: 4px;")
            note_lbl.setTextFormat(Qt.RichText)
            vlayout.addWidget(note_lbl)

        vlayout.addStretch()
        self.layout().insertWidget(self.layout().count() - 1, group)

    def _copy_cmd(self, cmd):
        from PySide6.QtWidgets import QApplication
        cb = QApplication.clipboard()
        cb.setText(cmd)
        QMessageBox.information(self, "Copied", f"Command copied to clipboard:\n\n{cmd}")
