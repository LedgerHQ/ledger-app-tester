import subprocess
import shutil
from pathlib import Path
from typing import Tuple


def run_cmd(cmd: str,
            cwd: Path,
            print_output: bool = True,
            no_throw: bool = False) -> Tuple[int, str]:
    stdout = ""
    print(f"[run_cmd] Running: {cmd} from {cwd}")

    ret = subprocess.run(cmd,
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,
                         universal_newlines=True,
                         cwd=cwd,
                         check=not no_throw)

    if ret.returncode:
        print(f"[run_cmd] Output:\n{ret.stdout}")
        stdout = f'''
###############################################################################
[run_cmd] Running: {cmd} from {cwd}"
###############################################################################
        ''' + ret.stdout
    else:
        stdout = ret.stdout.strip()

    return ret.returncode, stdout


def git_setup(repo_name: str, repo_ref: str, repo_url: str, workdir: Path) -> None:
    # Force clone in https over SSH
    GIT_CONFIG = ' -c  url."https://github.com/".insteadOf="git@github.com:" -c url."https://".insteadOf="git://"'

    if not Path.exists(workdir/Path(repo_name)):
        run_cmd(f"git {GIT_CONFIG} clone {repo_url} {repo_name}", cwd=workdir)
    else:
        run_cmd("git fetch", cwd=workdir/Path(repo_name))

    error, _ = run_cmd(f"git checkout {repo_ref}", cwd=workdir/Path(repo_name), no_throw=True)
    if error:
        print("Error: removing folder")
        shutil.rmtree(workdir/Path(repo_name))
        return

    error, _ = run_cmd(f"git {GIT_CONFIG} submodule update --init --recursive",
                       cwd=workdir/Path(repo_name),
                       no_throw=True)
    if error:
        print("Error: removing folder")
        shutil.rmtree(workdir/Path(repo_name))
        return


def merge_json(json1: dict, json2: dict, key: str):
    merged_data = []

    for obj1 in json1:
        merged_obj = obj1.copy()
        for obj2 in json2:
            if obj1[key] == obj2[key]:
                merged_obj.update(obj2)
                break
        merged_data.append(merged_obj)

    return merged_data
