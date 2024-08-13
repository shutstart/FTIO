import sys
import subprocess
import socket
import getopt
import os
import signal
import time
import threading
from rich.console import Console
from rich.panel import Panel
from rich.status import Status
from ftio.api.gekkoFs.jit.jitsettings import JitSettings

console = Console()


def is_port_in_use(port_number):
    try:
        # Run the netstat command and search for the port number
        netstat_output = subprocess.check_output(
            f"netstat -tlpn | grep ':{port_number} '",
            shell=True,
            stderr=subprocess.STDOUT,
        ).decode("utf-8")
        # If output is found, the port is in use
        if netstat_output:
            console.print(
                f"[bold red]Error: Port {port_number} is already in use...[/bold red]"
            )
            return True  # Port is in use
    except subprocess.CalledProcessError:
        # grep returns a non-zero exit status if it finds no matches
        console.print(f"[bold blue]Port {port_number} is available.[/bold blue]")
        return False  # Port is free


def check_port(settings: JitSettings):
    """Check if a port is available and terminate any existing process using it."""
    if is_port_in_use(settings.port):
        jit_print(
            f"[bold red]Error: Port {settings.port} is already in use on {settings.address_ftio}. Terminating existing process...[/]"
        )

        # Identify the process ID using the settings.port
        try:
            process_output = (
                subprocess.check_output(
                    f"netstat -nlp | grep :{settings.port} ", shell=True
                )
                .decode()
                .strip()
            )
            process_id = process_output.split()[6].split("/")[0]

            if process_id:
                jit_print(f"[bold yellow]Terminating process with PID: {process_id}[/]")
                os.kill(int(process_id), 9)
                jit_print(
                    f"[bold green]Using port {settings.port} on {settings.address_ftio}.[/]"
                )
                return 0
            else:
                jit_print(
                    f"[bold red]Failed to identify process ID for PORT {settings.port}.[/]"
                )
                exit(1)
        except subprocess.CalledProcessError as e:
            jit_print(f"[bold red]Failed to retrieve process information: {e}[/]")
            exit(1)
    else:
        jit_print(
            f"[bold green]Using port {settings.port} on {settings.address_ftio}.[/]"
        )


def parse_options(settings: JitSettings, args: list) -> None:

    try:
        opts, args = getopt.getopt(
            args,
            "a:p:n:t:l:i:e:xh",
            [
                "address=",
                "port=",
                "nodes=",
                "max-time=",
                "log-name=",
                "install-location=",
                "exclude=",
                "exclude-all",
                "help",
            ],
        )
    except getopt.GetoptError as err:
        console.print(f"[bold red]Error: {err}[/bold red]")
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-a", "--address"):
            settings.address_ftio = arg
        elif opt in ("-p", "--port"):
            settings.port = arg
        elif opt in ("-n", "--nodes"):
            settings.nodes = arg
        elif opt in ("-t", "--max-time"):
            settings.max_time = arg
        elif opt in ("-l", "--log-name"):
            settings.log_dir = arg
        elif opt in ("-i", "--install-location"):
            settings.install_location = arg
            install_all(settings)
        elif opt in ("-e", "--exclude"):
            jit_print("[bold yellow]>> Excluding: [/]")
            if not arg or arg.startswith("-"):
                settings.exclude_ftio = True
                console.print("- ftio")
            else:
                excludes = arg.split(",")
                for exclude in excludes:
                    if exclude == "ftio":
                        settings.exclude_ftio = True
                        console.print("- ftio")
                    elif exclude == "cargo":
                        settings.exclude_cargo = True
                        console.print("- cargo")
                    elif exclude in ("gkfs", "demon", "proxy"):
                        if exclude == "gkfs":
                            settings.exclude_demon = True
                            settings.exclude_proxy = True
                            console.print("- gkfs")
                        elif exclude == "demon":
                            settings.exclude_demon = True
                            console.print("- demon")
                        elif exclude == "proxy":
                            settings.exclude_proxy = True
                            console.print("- proxy")
                    elif exclude == "all":
                        settings.exclude_all = True
                        settings.update()
                        console.print("- all")
                    else:
                        console.print(
                            f"[bold green]JIT >>[bold red] Invalid exclude option: {exclude} [/]"
                        )
                        sys.exit(1)
        elif opt in ("-x", "--exclude-all"):
            settings.exclude_all = True
            settings.update()
        elif opt in ("-h", "--help"):
            error_usage(settings)
            sys.exit(1)
        else:
            console.print(f"[bold red]Invalid option: {opt}[/]")
            error_usage(settings)
            sys.exit(1)


def error_usage(settings: JitSettings):
    console.print(
        f"""
[bold]Usage: {sys.argv[0]} [OPTION] ... [/]
    -a | --address: X.X.X.X <string>
        default: [bold yellow]{settings.address_ftio}[/]
        Address where FTIO is executed. On a cluster, this is found 
        automatically by determining the address of node where FTIO 
        runs.

    -p | --port: XXXX <int>
        default: [bold yellow]{settings.port}[/]
        port for FTIO and GekkoFS.

    -n | --nodes: X <int>
        default: [bold yellow]{settings.nodes}[/]
        number of nodes to run the setup. In cluster mode, FTIO is 
        executed on a single node, while the rest (including the
        application) get X-1 nodes.

    -t | --max-time: X <int>
        default: [bold yellow]{settings.max_time}[/]
        max time for the execution of the setup in minutes.
    
    -l | --log-name: <str>
        default: Autoset to number of nodes and job ID
        if provided, sets the name of the directory where the logs are stored.

    -e | --exclude: <str>,<str>,...,<str>
        default: ftio
        If this flag is provided, the setup is executed without the tool(s).
        Supported options include: ftio, demon, proxy, gkfs (demon + proxy), 
        cargo, and all (same as -x).

    -x | --exclude-all
        default: [bold yellow]{settings.exclude_all}[/]
        If this flag is provided, the setup is executed without FTIO, 
        GekkoFS, and Cargo.

    -i | --install-location: full_path <str>
        default: [bold yellow]{settings.install_location}[/]
        Installs everything in the provided directory.

---- exit ----
    """
    )


def abort():
    console.print("[bold green]JIT [bold red] >>> Aborting installation[/]")
    exit(1)


def install_all(settings: JitSettings) -> None:
    with console.status("[bold green]Starting installation...") as status:
        try:
            # Create directory
            console.print("[bold green]JIT >>> Creating directory[/]")
            os.makedirs(settings.install_location, exist_ok=True)

            # Clone GKFS
            console.print("[bold green]JIT >>> Installing GEKKO[/]")
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--recurse-submodules",
                    "https://storage.bsc.es/gitlab/hpc/gekkofs.git",
                ],
                cwd=settings.install_location,
                check=True,
            )
            os.chdir(os.path.join(settings.install_location, "gekkofs"))
            subprocess.run(["git", "pull", "--recurse-submodules"], check=True)
            os.chdir(settings.install_location)

            # Build GKFS
            console.print("[bold green]JIT >>> Building GKFS[/]")
            subprocess.run(
                [
                    "gekkofs/scripts/gkfs_dep.sh",
                    "-p",
                    "default_zmq",
                    f"{settings.install_location}/iodeps/git",
                    f"{settings.install_location}/iodeps",
                ],
                check=True,
            )
            build_dir = os.path.join(settings.install_location, "gekkofs", "build")
            os.makedirs(build_dir, exist_ok=True)
            subprocess.run(
                [
                    "cmake",
                    "-DCMAKE_BUILD_TYPE=Release",
                    f"-DCMAKE_PREFIX_PATH={settings.install_location}/iodeps",
                    "-DGKFS_BUILD_TESTS=OFF",
                    f"-DCMAKE_INSTALL_PREFIX={settings.install_location}/iodeps",
                    "-DGKFS_ENABLE_CLIENT_METRICS=ON",
                    "..",
                ],
                cwd=build_dir,
                check=True,
            )
            subprocess.run(["make", "-j", "4", "install"], cwd=build_dir, check=True)

            console.print("[bold green]JIT >>> GEKKO installed[/]")

            console.print("[bold green]JIT >>> Installing Cereal[/]")
            subprocess.run(
                ["git", "clone", "https://github.com/USCiLab/cereal"],
                cwd=settings.install_location,
                check=True,
            )
            os.chdir(os.path.join(settings.install_location, "cereal"))
            build_dir = os.path.join(settings.install_location, "cereal", "build")
            os.makedirs(build_dir, exist_ok=True)
            subprocess.run(
                [
                    "cmake",
                    f"-DCMAKE_PREFIX_PATH={settings.install_location}/iodeps",
                    f"-DCMAKE_INSTALL_PREFIX={settings.install_location}/iodeps",
                    "..",
                ],
                cwd=build_dir,
                check=True,
            )
            subprocess.run(["make", "-j", "4", "install"], cwd=build_dir, check=True)

            # Install Cargo Dependencies: Thallium
            console.print("[bold green]JIT >>> Installing Thallium[/]")
            subprocess.run(
                ["git", "clone", "https://github.com/mochi-hpc/mochi-thallium"],
                cwd=settings.install_location,
                check=True,
            )
            os.chdir(os.path.join(settings.install_location, "mochi-thallium"))
            build_dir = os.path.join(
                settings.install_location, "mochi-thallium", "build"
            )
            os.makedirs(build_dir, exist_ok=True)
            subprocess.run(
                [
                    "cmake",
                    f"-DCMAKE_PREFIX_PATH={settings.install_location}/iodeps",
                    f"-DCMAKE_INSTALL_PREFIX={settings.install_location}/iodeps",
                    "..",
                ],
                cwd=build_dir,
                check=True,
            )
            subprocess.run(["make", "-j", "4", "install"], cwd=build_dir, check=True)

            # Clone and Build Cargo
            console.print("[bold green]JIT >>> Installing Cargo[/]")
            subprocess.run(
                ["git", "clone", "https://storage.bsc.es/gitlab/hpc/cargo.git"],
                cwd=settings.install_location,
                check=True,
            )
            os.chdir(os.path.join(settings.install_location, "cargo"))
            replace_line_in_file(
                "src/master.cpp", 332, f'  auto patternFile = "{settings.regex_file}";'
            )

            build_dir = os.path.join(settings.install_location, "cargo", "build")
            os.makedirs(build_dir, exist_ok=True)
            subprocess.run(
                [
                    "cmake",
                    "-DCMAKE_BUILD_TYPE=Release",
                    f"-DCMAKE_PREFIX_PATH={settings.install_location}/iodeps",
                    f"-DCMAKE_INSTALL_PREFIX={settings.install_location}/iodeps",
                    "..",
                ],
                cwd=build_dir,
                check=True,
            )
            subprocess.run(["make", "-j", "4", "install"], cwd=build_dir, check=True)

            console.print("[bold green]JIT >>> Cargo installed[/]")

            # Build IOR
            console.print("[bold green]JIT >>> Installing IOR[/]")
            subprocess.run(
                ["git", "clone", "https://github.com/hpc/ior.git"],
                cwd=settings.install_location,
                check=True,
            )
            os.chdir(os.path.join(settings.install_location, "ior"))
            subprocess.run(["./bootstrap"], check=True)
            subprocess.run(["./configure"], check=True)
            subprocess.run(["make", "-j", "4"], check=True)

            console.print("[bold green]JIT >> Installation finished[/]")
            console.print("\n>> Ready to go <<")
            console.print("Call: ./jit.sh -n NODES -t MAX_TIME")

        except subprocess.CalledProcessError as e:
            console.print("[bold green]JIT [bold red] >>> Error encountered: {e}[/]")
            abort()


def replace_line_in_file(file_path, line_number, new_line_content):
    try:
        # Read the existing file content
        with open(file_path, "r") as file:
            lines = file.readlines()

        # Replace the specific line (line_number - 1 because list indices start at 0)
        if line_number - 1 < len(lines):
            lines[line_number - 1] = new_line_content + "\n"
        else:
            raise IndexError(
                "Line number exceeds the total number of lines in the file."
            )

        # Write the modified content back to the file
        with open(file_path, "w") as file:
            file.writelines(lines)

        print(f"Successfully replaced line {line_number} in {file_path}.")

    except FileNotFoundError:
        print(f"Error: The file {file_path} does not exist.")
    except IndexError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def cancel_jit_jobs():
    # Check if the hostname contains 'cpu' or 'mogon'
    hostname = subprocess.check_output("hostname", shell=True).decode().strip()
    if "cpu" in hostname or "mogon" in hostname:
        # Get the list of job IDs with the name "JIT"
        try:
            jit_jobs = (
                subprocess.check_output(
                    "squeue --me --name=JIT --format=%A", shell=True
                )
                .decode()
                .strip()
                .split("\n")[1:]
            )
        except subprocess.CalledProcessError:
            jit_jobs = []

        if not jit_jobs:
            return

        # Print the list of JIT jobs
        job_list = "\n".join(jit_jobs)
        console.print(
            "[bold green]JIT [bold yellow]>> The following jobs with the name 'JIT' were found:[/]"
        )
        console.print(job_list)

        # Prompt the user to confirm cancellation
        confirmation = (
            input("Do you want to cancel all 'JIT' jobs? (yes/no): ").strip().lower()
        )

        if confirmation in {"yes", "y", "ye"}:
            for job_id in jit_jobs:
                subprocess.run(f"scancel {job_id}", shell=True, check=True)
                console.print(
                    f"[bold green]JIT [bold cyan]>> Cancelled job ID {job_id}[/]"
                )
            console.print(
                "[bold green]JIT [bold green]>> All 'JIT' jobs have been cancelled.[/]"
            )
        else:
            console.print("[bold green]JIT [bold yellow]>> No jobs were cancelled.[/]")


def get_pid(settings: JitSettings, name: str, pid: int):
    if settings.cluster == True:
        cmd = f"ps aux | grep 'srun' | grep '{settings.jit_id}' | grep '$1' | grep -v grep | tail -1 | awk '{{print $2}}'"
        pid = subprocess.run(cmd, shell=True, universal_newlines=True, check=True)
        print(pid)
        print(name)

    if name.lower() in "cargo":
        settings.cargo_pid = pid
        console.print(f"[green bold]JIT >>> Cargo PID: {pid}[/]")
    elif name.lower() in "gkfs_demon":
        settings.gekko_demon_pid = pid
        console.print(f"[green bold]JIT >>> Gekko demon PID: {pid}[/]")
    elif name.lower() in "gkfs_proxy":
        settings.gekko_proxy_pid = pid
        console.print(f"[green bold]JIT >>> Gekko proxy PID: {pid}[/]")
    elif name.lower() in "ftio" or name.lower() in "predictor_jit":
        settings.ftio_pid = pid
        console.print(f"[green bold]JIT >>> Ftio PID: {pid}[/]")


def relevant_files(settings: JitSettings, verbose: bool = False):

    if verbose:  # Mimicking checking for the number of arguments
        console.print(f"[bold green] JIT [bold cyan]>> Setting up ignored files[/]")

    # Create or update the regex file with the settings.regex_match
    with open(settings.regex_file, "w") as file:
        file.write(f"{settings.regex_match}\n")

    if verbose:
        console.print(
            f"[bold green] JIT [cyan]>> Files that match {settings.regex_match} are ignored [/]"
        )

    # Display the contents of the regex file
    with open(settings.regex_file, "r") as file:
        content = file.read()
    if settings.debug:
        console.print(
            f"[bold green] JIT [cyan]>> content of {settings.regex_file}: \n{content}[/]"
        )


def reset_relevant_files(settings: JitSettings) -> None:
    if settings.cluster:
        console.print(f"[bold green] JIT [bold cyan]>> Resetting ignored files[/]")
        # Write the default regex pattern to the file
        with open(settings.regex_file, "w") as file:
            file.write(".*\n")
        # Optionally console.print the contents of the regex file
        # with open(settings.regex_file, 'r') as file:
        #     content = file.read()
        # console.print(f"[bold green] JIT [bold cyan]>> cat {settings.regex_file}: \n{content} [/]\n")


def total_time(log_dir):
    time_log_file = os.path.join(log_dir, "time.log")

    # Calculate total time from the log file
    try:
        with open(time_log_file, "r") as file:
            lines = file.readlines()
        total_time = sum(float(line.split()[1]) for line in lines if "seconds" in line)
    except FileNotFoundError:
        total_time = 0

    # Print and append total time to the log file
    result = f"\n JIT --> Total Time: {total_time}\n"
    console.print("[bold green]" + result + "[/]")
    with open(time_log_file, "a") as file:
        file.write(result)


def allocate(settings: JitSettings) -> None:
    settings.app_nodes = 1
    if settings.cluster:
        # Allocating resources
        console.print(
            "\n[bold green]JIT [green] ####### Allocating resources[/]",
            style="bold green",
        )

        call = f"salloc -N {settings.nodes} -t {settings.max_time} {settings.alloc_call_flags}"
        console.print(f"[bold green]JIT [cyan] >> Executing: {call} [/]")

        # Execute the salloc command
        subprocess.run(call, shell=True, check=True)

        # Get JIT_ID
        try:
            result = subprocess.run(
                "squeue -o '%.18i %.9P %.8j %.8u %.2t %.10M %.6D %R' | grep ' JIT ' | sort -k1,1rn | head -n 1 | awk '{print $1}'",
                shell=True,
                capture_output=True,
                text=True,
                check=True,
            )
            settings.jit_id = int(result.stdout.strip())
        except subprocess.CalledProcessError:
            settings.jit_id = 0

        # Get NODES_ARR
        if settings.jit_id:
            try:
                nodes_result = subprocess.run(
                    f"scontrol show hostname $(squeue -j {settings.jit_id} -o '%N' | tail -n +2)",
                    shell=True,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                nodes_arr = nodes_result.stdout.splitlines()
            except subprocess.CalledProcessError:
                nodes_arr = []

            # Write to hostfile_mpi
            with open(os.path.expanduser("~/hostfile_mpi"), "w") as file:
                file.write("\n".join(nodes_arr) + "\n")

            if nodes_arr:
                # Get FTIO node
                settings.ftio_node = nodes_arr[-1]
                # Get node for single commands
                settings.single_node = nodes_arr[0]

                if len(nodes_arr) > 1:
                    settings.ftio_node_command = f"--nodelist={settings.ftio_node}"
                    settings.app_nodes_command = f"--nodelist={','.join(n for n in nodes_arr if n != settings.ftio_node)}"
                    settings.single_node_command = f"--nodelist={settings.single_node}"
                    settings.app_nodes = len(nodes_arr) - 1

                    # Remove FTIO node from hostfile_mpi
                    with open(os.path.expanduser("~/hostfile_mpi"), "r") as file:
                        lines = file.readlines()
                    with open(os.path.expanduser("~/hostfile_mpi"), "w") as file:
                        file.writelines(
                            line for line in lines if line.strip() != settings.ftio_node
                        )

                console.print(
                    f"[bold green]JIT [green] >> JIT Job Id: {settings.jit_id} [/]"
                )
                console.print(
                    f"[bold green]JIT [green] >> Allocated Nodes: {len(nodes_arr)} [/]"
                )
                console.print(
                    f"[bold green]JIT [green] >> FTIO Node: {settings.ftio_node} [/]"
                )
                console.print(
                    f"[bold green]JIT [green] >> APP Node command: {settings.app_nodes_command} [/]"
                )
                console.print(
                    f"[bold green]JIT [green] >> FTIO Node command: {settings.ftio_node_command} [/]"
                )

                # Print contents of hostfile_mpi
                with open(os.path.expanduser("~/hostfile_mpi"), "r") as file:
                    hostfile_content = file.read()
                console.print(
                    f"[bold green]JIT [cyan] >> content of ~/hostfile_mpi: \n{hostfile_content} [/]"
                )
        else:
            console.print(
                "[bold gree]JIT [bold red]>> JIT_ID could not be retrieved[/]"
            )

    else:
        settings.procs = settings.nodes
        settings.nodes = 1
        console.print(
            f"[bold green]JIT [bold cyan]>> Number of processes: {settings.procs} [/]"
        )


# Function to handle SIGINT (Ctrl+C)
def handle_sigint(settings: JitSettings):
    console.print("[bold green]JIT > Keyboard interrupt detected. Exiting script.[/]")
    soft_kill(settings)
    hard_kill(settings)
    if settings.cluster:
        execute(f"scancel {settings.jit_id}")
    sys.exit(0)


def soft_kill(settings: JitSettings) -> None:
    console.print("\n[bold green]JIT[bold green] ####### Soft kill [/]")

    if settings.exclude_ftio == False:
        try:
            shut_down(settings, "FTIO", settings.ftio_pid)
            console.print("[bold green]JIT[bold cyan] >> killed FTIO [/]")
        except:
            console.print("[bold green]JIT[bold cyan] >> Unable to soft kill FTIO [/]")

    if settings.exclude_demon == False:
        try:
            shut_down(settings, "GEKKO", settings.gekko_demon_pid)
            console.print("[bold green]JIT[bold cyan] >> killed GEKKO DEMON [/]")
        except:
            console.print("[bold green]JIT[bold cyan] >> Unable to soft kill GEKKO DEMON [/]")

    if settings.exclude_proxy == False:
        try:
            shut_down(settings, "GEKKO", settings.gekko_proxy_pid)
            console.print("[bold green]JIT[bold cyan] >> killed GEKKO PROXY [/]")
        except:
            console.print("[bold green]JIT[bold cyan] >> Unable to soft  kill GEKKO PROXY [/]")

    if settings.exclude_cargo == False:
        try:
            shut_down(settings, "CARGO", settings.cargo_pid)
            console.print("[bold green]JIT[bold cyan] >> killed CARGO [/]")
        except:
            console.print("[bold green]JIT[bold cyan] >> Unable to soft kill CARGO [/]")


def hard_kill(settings) -> None:
    console.print(f"\n[bold green]####### Hard kill[/]")

    if settings.cluster:
        # Cluster environment: use `scancel` to cancel the job
        call = f"scancel {settings.jit_id}"
        execute(call)
    else:
        # Non-cluster environment: use `kill` to terminate processes
        processes = [
            settings.gkfs_demon,
            settings.gkfs_proxy,
            settings.cargo,
            f"{os.path.dirname(settings.ftio_activate)}/predictor_jit",
        ]

        for process in processes:
            try:
                # Find process IDs and kill them
                kill_command = f"ps -aux | grep {process} | grep -v grep | awk '{{print $2}}' | xargs kill"
                while(kill_command):
                    subprocess.run(
                        kill_command, shell=True, capture_output=True, text=True, check=True
                    )
                    kill_command = f"ps -aux | grep {process} | grep -v grep | awk '{{print $2}}' | xargs kill"
            except Exception as e:
                console.print(f"[bold red]{process} already dead[/]")



def shut_down(settings, name, pid):
    console.print(f"Shutting down {name} with PID {pid}")
    if pid:
        try:
            # Terminate the process
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            print(f"Process with PID {pid} does not exist.")
        except PermissionError:
            print(f"Permission denied to kill process with PID {pid}.")
        except Exception as e:
            print(f"An error occurred: {e}")

        # Wait for the process to terminate if in a cluster
        if settings.cluster == True:
            execute(f"wait {pid}")


def log_dir(settings):
    if not settings.log_dir:
        # Define default LOG_DIR if not set
        settings.log_dir = f"logs_nodes{settings.nodes}_Jobid{settings.jit_id}"

    # Create directory if it does not exist
    os.makedirs(settings.log_dir, exist_ok=True)

    # Resolve and return the absolute path of LOG_DIR
    settings.log_dir = os.path.abspath(settings.log_dir)


def get_address_ftio(settings: JitSettings) -> None:
    # Get Address and port
    jit_print("####### Getting FTIO ADDRESS")
    if settings.cluster == True:
        call = f"srun --jobid={settings.jit_id} {settings.ftio_node_command} --disable-status -N 1 --ntasks=1 --cpus-per-task=1 --ntasks-per-node=1 --overcommit --overlap --oversubscribe --mem=0 ip addr | grep ib0 | awk '{{print $2}}' | cut -d'/' -f1 | tail -1"
        jit_print(f"[bold cyan]>> Executing: {call}")
        try:
            result = subprocess.run(
                call, shell=True, capture_output=True, text=True, check=True
            )
            settings.address_ftio = result.stdout.strip()
        except subprocess.CalledProcessError as e:
            jit_print(f"[bold red]>>Error occurred: {e}")
            settings.address_ftio = ""

    jit_print(f">> Address FTIO: {settings.address_ftio}")


def get_address_cargo(settings: JitSettings) -> None:
    jit_print("####### Getting Cargo ADDRESS")
    if settings.cluster == True:
        call = f"srun --jobid={settings.jit_id} {settings.single_node_command} --disable-status -N 1 --ntasks=1 --cpus-per-task=1 --ntasks-per-node=1 --overcommit --overlap --oversubscribe --mem=0 ip addr | grep ib0 | awk '{{print $2}}' | cut -d'/' -f1 | tail -1"
        jit_print(f"[bold cyan]>> Executing: {call}")
        try:
            result = subprocess.run(
                call, shell=True, capture_output=True, text=True, check=True
            )
            settings.address_cargo = result.stdout.strip()
            settings.cargo_server = f"ofi+sockets://{settings.address_cargo}:62000"
        except subprocess.CalledProcessError as e:
            jit_print(f"[bold red]>>Error occurred: {e}")
            settings.address_cargo = ""
            settings.cargo_server = ""
    else:
        settings.cargo_server = f"ofi+tcp://{settings.address_cargo}:62000"

    jit_print(f">> Address CARGO: {settings.address_cargo}")
    jit_print(f">> CARGO server:  {settings.cargo_server} ")


def print_settings(settings) -> None:
    ftio_status = f"[bold green]ON[/]"
    gkfs_demon_status = f"[bold green]ON[/]"
    gkfs_proxy_status = f"[bold green]ON[/]"
    cargo_status = f"[bold green]ON[/]"

    # Default settings text
    ftio_text = f"""
├─ ftio activate  : {settings.ftio_activate}
├─ address ftio   : {settings.address_ftio}
├─ port           : {settings.port}
├─ # nodes        : 1
└─ ftio node      : {settings.ftio_node_command.replace('--nodelist=', '')}"""

    gkfs_demon_text = f"""
├─ gkfs demon     : {settings.gkfs_demon}
├─ gkfs intercept : {settings.gkfs_intercept}
├─ gkfs mntdir    : {settings.gkfs_mntdir}
├─ gkfs rootdir   : {settings.gkfs_rootdir}
├─ gkfs hostfile  : {settings.gkfs_hostfile}"""

    gkfs_proxy_text = f"""
├─ gkfs proxy     : {settings.gkfs_proxy}
└─ gkfs proxyfile : {settings.gkfs_proxyfile}"""

    cargo_text = f"""
├─ cargo          : {settings.cargo}
├─ cargo cli      : {settings.cargo_cli}
├─ stage in path  : {settings.stage_in_path}
└─ address cargo  : {settings.address_cargo}"""

    if settings.exclude_ftio:
        ftio_text = """
├─ ftio activate  : [yellow]none[/]
├─ address ftio   : [yellow]none[/]
├─ port           : [yellow]none[/]
├─ # nodes        : [yellow]none[/]
└─ ftio node      : [yellow]none[/]"""
        ftio_status = "[bold yellow]off[/]"

    if settings.exclude_demon:
        gkfs_demon_text = """
├─ gkfs demon     : [yellow]none[/]
├─ gkfs intercept : [yellow]none[/]
├─ gkfs mntdir    : [yellow]none[/]
├─ gkfs rootdir   : [yellow]none[/]
├─ gkfs hostfile  : [yellow]none[/]"""
        gkfs_demon_status = "[bold yellow]off[/]"

    if settings.exclude_proxy:
        gkfs_proxy_text = """
├─ gkfs proxy     : [yellow]none[/]
└─ gkfs proxyfile : [yellow]none[/]"""
        gkfs_proxy_status = "[bold yellow]off[/]"

    if settings.exclude_cargo:
        cargo_text = """
├─ cargo location : [yellow]none[/]
├─ cargo cli      : [yellow]none[/]
├─ stage in path  : [yellow]none[/]
└─ address cargo  : [yellow]none[/]"""
        cargo_status = "[bold yellow]off[/]"

    # print settings
    text = f"""
[bold green]Settings
##################[/]
[bold green]setup[/]
├─ logs dir       : {settings.log_dir}
├─ pwd            : {os.getcwd()}
├─ ftio           : {ftio_status}
├─ gkfs demon     : {gkfs_demon_status}
├─ gkfs proxy     : {gkfs_proxy_status}
├─ cargo          : {cargo_status}
├─ cluster        : {settings.cluster}
├─ total nodes    : {settings.nodes}
├─ app nodes      : {settings.app_nodes}
├─ ftio nodes     : 1
├─ procs          : {settings.procs}
├─ max time       : {settings.max_time}
└─ job id         : {settings.jit_id}

[bold green]ftio[/]{ftio_text}

[bold green]gekko[/]{gkfs_demon_text}{gkfs_proxy_text}

[bold green] cargo[/]{cargo_text}

[bold green]app[/]
├─ precall        : {settings.precall}
├─ app_call       : {settings.app_call}
├─ # nodes        : {settings.app_nodes}
└─ app nodes      : {settings.app_nodes_command.replace('--nodelist=', '')}
[bold green]##################[/]
"""
    console.print(text)
    print_to_file(text, os.path.join(settings.log_dir, "settings.log"))


def print_to_file(text, file):
    remove = ["bold", "green", "yellow", "red", "cyan", "[/]", "[ ]", "[]"]
    for r in remove:
        text = text.replace(r, "")

    with open(file, "w") as file:
        file.write(text)


def jit_print(s: str):
    console.print(f"[bold green]JIT[/][green] {s}[/]")


def execute(call) -> None:
    jit_print(f">> Executing {call}")
    try:
        # subprocess.run(call, shell=True, capture_output=True, text=True, check=True)
        # process = subprocess.Popen(call, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out = subprocess.run(call, shell=True, text=True, check=True, executable='/bin/bash')
    except subprocess.CalledProcessError as e:
        error_message = (
            f"[red]Command failed:[/red] {call}\n"
            f"[red]Exit code:[/red] {e.returncode}\n"
            f"[red]Output:[/red] {e.stdout.strip()}\n"
            f"[red]Error:[/red] {e.stderr.strip()}"
        )
        console.print(f"[red]{error_message}\n[/]")
        handle_sigint
        raise

def execute_and_log(call,log_file) -> float:
    log_message = f">> Executing command: {call}\n"
    jit_print("[cyan]"+log_message)
    start = time.time()
    end = start
    try:
        out = subprocess.run(call, shell=True, capture_output=True, text=True, check=True, executable='/bin/bash')
        end = time.time()
        log_message += f"Output:\n{out.stdout}\n"
    except subprocess.CalledProcessError as e:
        log_message += f"Error:\n{e.stderr}\n"
        error_message = (
            f"[red]Command failed:[/red] {call}\n"
            f"[red]Exit code:[/red] {e.returncode}\n"
            f"[red]Output:[/red] {e.stdout.strip()}\n"
            f"[red]Error:[/red] {e.stderr.strip()}"
        )
        console.print(f"[red]{error_message}[/]")
        handle_sigint
        raise
    finally:
        # Write the log message to the file
        with open(log_file, "a") as file:
            file.write(log_message)
    return end - start


def execute_background(call: str, log_file: str = "", log_err_file: str = ""):
    """executes a call in the background and sets up a log dir

    Args:
        call (str): call to execute
        log_dir (str, optional): log dir directory. Defaults to "".
        error_dir (str, optional): error die directory. Defaults to "".

    Returns:
        _type_: _description_
    """
    jit_print(f"[cyan]>> Executing {call}")
    with open(log_file, "a") as file:
            file.write(f">> Executing {call}")
            
    if log_file and log_err_file:
        with open(log_file, "a") as log_out:
            with open(log_err_file, "w") as log_err:
                process = subprocess.Popen(
                    call, shell=True, stdout=log_out, stderr=log_err
                )
    elif log_file:
        with open(log_file, "a") as log_out:
            process = subprocess.Popen(
                call, shell=True, stdout=log_out, stderr=subprocess.STDOUT
            )
    else:
        process = subprocess.Popen(
            call, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
    return process


def execute_and_wait_line(call: str, filename: str, target_line: str):
    execute(call)
    wait_for_line(filename, target_line)


def monitor_log_file(file, src=""):
    monitor_thread = threading.Thread(target=print_file, args=(file, src))
    monitor_thread.daemon = True
    monitor_thread.start()


def print_file(file, src=""):
    """Continuously monitor the log file for new lines and print them."""
    color = ""
    if src:
        if "demon" in src:
            color = "[purple4]"
        elif "proxy" in src:
            color = "[deep_pink1]"
        elif "ftio" in src:
            color = "[deep_sky_blue1]"

    with open(file, "r") as file:
        # Go to the end of the file
        file.seek(0, os.SEEK_END)
        while True:
            line = file.readline()
            if line and len(line)> 0:
                if not src or "cargo" in src:
                    print(line.rstrip())
                else:
                    console.print(
                        Panel.fit(
                            color + line.rstrip(),
                            title=src,
                            style="white",
                            border_style="white",
                            title_align="left",
                        )
                    )
            else:
                time.sleep(0.1)  # Sleep briefly to avoid high CPU usage


def wait_for_file(filename: str, timeout: int = 60) -> None:
    """Waits for a file to be created

    Args:
        file (str): absolute file path
    """
    start_time = time.time()
    with Status(
        f"[cyan]Waiting for {filename} to be created...\n", console=console
    ) as status:
        while not os.path.isfile(filename):
            passed_time = int(time.time() - start_time)
            if passed_time >= timeout:
                status.update("Timeout reached")
                console.print("[bold green]JIT [bold red]>> Timeout reached[/]")
                handle_sigint
                return

            status.update(
                f"[cyan]Waiting for {filename} to be created... ({passed_time}/{timeout}) s"
            )
            time.sleep(1)  # Wait for 1 second before checking again

        # When the file is created, update the status
        status.update(f"{filename} has been created.")
        console.print(f"[bold green]JIT [/]>>{filename} has been created.")


def wait_for_line(filename: str, target_line: str, timeout: int = 60) -> None:
    """
    Waits for a specific line to appear in a log file

    Args:
        filename (str): The path to the log file.
        target_line (str): The line of text to wait for.
    """
    start_time = time.time()

    with open(filename, "r") as file:
        # Move to the end of the file to start monitoring
        # file.seek(0, 2)  # Go to the end of the file and look at the last 10 entris
        try:
            file.seek(-2, os.SEEK_END)
        except:
            file.seek(0, 0)  # Go to the end of the file and look at the last 10 entris

        with Status(f"[cyan]Waiting for line to appear...", console=console) as status:
            while True:
                line = file.readline()
                if not line:
                    # If no line, wait and check again
                    time.sleep(0.1)
                    passed_time = int(time.time() - start_time)
                    if passed_time >= timeout:
                        status.update("Timeout reached.")
                        console.print(
                            "[bold green]JIT [bold red]>> Timeout reached. [/]"
                        )
                        handle_sigint
                        return
                    status.update(
                        f"[cyan]Waiting for line to appear... ({passed_time}/{timeout})"
                    )
                    continue

                if target_line in line:
                    status.update(f"Found target line: '{target_line}'")
                    console.print(
                        f"\n[bold green]JIT [/]>> Found target line: '{target_line}'"
                    )
                    break


def create_hostfile(settings):
    jit_print(f"[cyan]>> Cleaning Hostfile: {settings.gkfs_hostfile}")

    try:
        if os.path.exists(settings.gkfs_hostfile):
            os.remove(settings.gkfs_hostfile)
        else:
            jit_print("[blue]>> No hostfile found[/blue]")

    except Exception as e:
        jit_print(f"[bold red]Error removing hostfile:[/bold red] {e}")

    # # Optionally, recreate the hostfile and populate it if needed
    # try:
    #     # Create the hostfile (if needed)
    #     # with open(settings.gkfs_hostfile, 'w') as file:
    #     #     for node in settings.nodes_arr[:-1]:  # Exclude the last element
    #     #         file.write(f"cpu{node}\n")
    #     # console.print(f"[cyan]>> Creating Hostfile: {settings.gkfs_hostfile}")
    #     pass
    # except Exception as e:
    #     console.print(f"[bold red]Error creating hostfile:[/bold red] {e}")


def format_time(runtime):
    """Format the runtime in a more readable way."""
    hours, remainder = divmod(runtime, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours)}h {int(minutes)}m {seconds:.2f}s"


def elapsed_time(settings: JitSettings, name, runtime):
    """Calculate and print the elapsed time."""

    runtime_formatted = format_time(runtime)
    log_message = (
        f"\n\n[cyan]############[JIT]##############\n"
        f"# {name}\n"
        f"# time: [yellow]{runtime_formatted} [cyan]\n"
        f"# [yellow]{runtime} [cyan]seconds\n"
        f"##############################\n\n"
    )
    console.print(log_message)

    # Write to log file
    print_to_file(
        log_message,
        os.path.join(settings.log_dir, "time.log"),
    )


def check(settings: JitSettings):
    try:
        files = subprocess.check_output(
            f"LD_PRELOAD={settings.gkfs_intercept} LIBGKFS_HOSTS_FILE={settings.gkfs_hostfile} ls {settings.gkfs_mntdir}",
            shell=True,
            text=True,
        )
        jit_print(f"[cyan]>> geko_ls {settings.gkfs_mntdir}: [/]\n{files}")
    except subprocess.CalledProcessError as e:
        jit_print(f"[red]>> Failed to list files in {settings.gkfs_mntdir}: {e}[/]")


def check_setup(settings:JitSettings):
    
    if not settings.exclude_all:

        # Display MPI hostfile
        if settings.cluster:
            mpi_hostfile_path = os.path.expanduser('~/hostfile_mpi')
            with open(mpi_hostfile_path, 'r') as file:
                mpi_hostfile_content = file.read()
            console.print(f"[cyan]>> MPI hostfile:\n{mpi_hostfile_content}[/]")

        # Display GekkoFS hostfile
        gekkofs_hostfile = settings.gkfs_hostfile
        with open(gekkofs_hostfile, 'r') as file:
            gekkofs_hostfile_content = file.read()
        console.print(f"[cyan]>> Gekko hostfile:\n{gekkofs_hostfile_content}[/]")

        # # List files in GKFS_MNTDIR
        # ls_command = f"LD_PRELOAD={settings.gkfs_intercept} LIBGKFS_HOSTS_FILE={gekkofs_hostfile} ls {settings.gkfs_mntdir}"
        # files = subprocess.check_output(ls_command, shell=True).decode()
        # console.print(f"[cyan]>> geko_ls {gkfs_mntdir}: \n{files}[/]")

        # # Run MPI exec test script
        # procs = settings.procs
        # if settings.cluster:
        #     test_script_command = (f"mpiexec -np {procs} --oversubscribe --hostfile {mpi_hostfile_path} "
        #                         f"--map-by node -x LIBGKFS_LOG=errors -x LD_PRELOAD={settings.gkfs_intercept} "
        #                         f"-x LIBGKFS_HOSTS_FILE={gekkofs_hostfile} -x LIBGKFS_PROXY_PID_FILE={settings.gkfs_proxyfile} "
        #                         f"/home/tarrafah/nhr-admire/tarraf/FTIO/ftio/api/gekkoFs/scripts/test.sh")
        #     console.print(f"[cyan]>> statx:[/]")
        #     execute(test_script_command)

                    
        #     srun_command = (f"srun --export=LIBGKFS_HOSTS_FILE={settings.gkfs_hostfile},LD_LIBRARY_PATH={os.environ.get('LD_LIBRARY_PATH')},"
        #                     f"LD_PRELOAD={settings.gkfs_intercept} --jobid={settings.jit_id} {settings.app_nodes_command} --disable-status "
        #                     f"-N 1 --ntasks=1 --cpus-per-task=1 --ntasks-per-node=1 --overcommit --overlap --oversubscribe --mem=0 "
        #                     f"/usr/bin/ls {settings.gkfs_mntdir}")
        #     files2 = subprocess.check_output(srun_command, shell=True).decode()
        #     console.print(f"[cyan]>> srun ls {settings.gkfs_mntdir}: \n{files2}[/]")

        # Note: The commented out command for `mpirun` is not included in this translation.

    # Pause for 1 second
    time.sleep(1)



def update_hostfile_mpi(settings:JitSettings):
        # Command to get the list of hostnames for the job
    squeue_command = f"squeue -j {settings.jit_id} -o '%N' | tail -n +2"
    scontrol_command = f"scontrol show hostname $({squeue_command})"
    
    # Execute the command and capture the hostnames
    hostnames = subprocess.check_output(scontrol_command, shell=True).decode().splitlines()

    # Path to the output file
    hostfile_mpi_path = os.path.expanduser("~/hostfile_mpi")
    
    # Write the hostnames to the file, excluding the Ftio node
    with open(hostfile_mpi_path, 'w') as hostfile:
        for hostname in hostnames:
            if hostname.strip() != settings.ftio_node:
                hostfile.write(hostname + '\n')