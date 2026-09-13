"""register_with_root.py — register_with_root(root_ip) for ClusterWorker."""
import platform as plat
from common.loghub import LogHub
from common.protocol import ControlProtocol, MSG_REGISTER, MSG_REGISTER_ACK


class RegisterWithRootMixin:
    @LogHub.log_call("WORKER")
    def register_with_root(self, root_ip):
        if root_ip is None:
            return False
        try:
            self.conn = ControlProtocol()
            self.conn.connect(root_ip, self.ctrl_port)
            if self.ui:
                self.ui.set_connection("connecting", root_ip=root_ip)

            self.conn.send(MSG_REGISTER,
                hostname=self.hostname,
                platform=self.platform,
                arch=plat.machine(),
                cpu_cores=self.cpu_cores,
                ram_total=self.ram_total,
                ram_available=self.ram_available,
                rpc_port=self.rpc_port,
            )

            resp = self.conn.recv()
            if resp and resp.get("type") == MSG_REGISTER_ACK:
                self.registered = True
                self.root_ip = root_ip
                self.log(f"Registered with root at {root_ip}", notify=True)
                if self.ui:
                    self.ui.set_connection("connected", root_ip=root_ip, registered=True)
                    self.ui.set_service("connection", "running", f"root: {root_ip}")
                return True
            self.log(f"Registration rejected by root at {root_ip}")
            if self.ui:
                self.ui.set_connection("error", root_ip=root_ip)
            return False
        except Exception as e:
            self.log(f"Registration failed: {e}")
            if self.ui:
                self.ui.set_connection("error", root_ip=root_ip)
            return False
