"""Run a command inside the staging server container (namespace ocs-two-lives, deployment mc).

With a namespace key at ~/.kube/ocs-two-lives.yaml (or $TTL_KUBECONFIG) it uses kubectl straight to the K3s API
over Tailscale: no SSH, so no Tailscale SSH re-checks. Without one it goes over SSH to the node like before.
The key only reaches this namespace (ServiceAccount ttl-operator in the Homelab repo's ops.yaml).
"""
import os
import shutil
import subprocess
from pathlib import Path

NS = "ocs-two-lives"
NODE = os.environ.get("TTL_NODE", "root@100.109.28.21")
KUBECONFIG = Path(os.environ.get("TTL_KUBECONFIG", Path.home() / ".kube" / "ocs-two-lives.yaml"))


def kubectl() -> str:
    found = shutil.which("kubectl")
    docker = Path("C:/Program Files/Docker/Docker/resources/bin/kubectl.exe")
    return found or (str(docker) if docker.exists() else "kubectl")


def mc(command: str) -> subprocess.CompletedProcess:
    """`command` is a shell command line run in the server container; stdout comes back as bytes."""
    if KUBECONFIG.is_file():
        return subprocess.run([kubectl(), "--kubeconfig", str(KUBECONFIG), "-n", NS, "exec", "deploy/mc", "--",
                               "sh", "-c", command], capture_output=True)
    return subprocess.run(["ssh", "-n", "-o", "ConnectTimeout=10", "-o", "LogLevel=ERROR", NODE,
                           f"k3s kubectl -n {NS} exec deploy/mc -- {command}"], capture_output=True)
