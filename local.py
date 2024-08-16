import os  
import subprocess  
import sys  
import app.constants as constants

def create_virtualenv():  
    venv_dir = os.path.join(os.path.dirname(__file__), 'venv')  

    if not os.path.exists(venv_dir):  
        print("Creating virtual environment...")  
        subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)  
    else:  
        print("Virtual environment already exists.")  

    return venv_dir  

def modify_permissions(venv_dir):  
    activate_script = os.path.join(venv_dir, 'bin', 'activate')  

    if os.path.exists(activate_script):  
        print(f"Modifying permissions for {activate_script}...")  
        subprocess.run(['sudo', 'chmod', '+x', activate_script], check=True)  
    else:  
        raise FileNotFoundError(f"The activation script `{activate_script}` was not found.")  

def set_rw_permissions(path):  
    if os.path.exists(path):  
        print(f"Setting read, write, and execute permissions for {path} using sudo...")  
        subprocess.run(['sudo', 'chmod', '0777', path], check=True)  
    else:  
        raise FileNotFoundError(f"The path `{path}` does not exist.")  


def activate_and_install_requirements(venv_dir):  
    activate_script = os.path.join(venv_dir, 'bin', 'activate')  
    pip_executable = os.path.join(venv_dir, 'bin', 'pip')  

    requirements_file = os.path.join(os.path.dirname(__file__), 'requirements.txt')  
    if not os.path.exists(requirements_file):  
        raise FileNotFoundError(f"The requirements file `{requirements_file}` does not exist.")  

    # Construct and run the command to activate the virtual environment and install the requirements  
    command = f"source {activate_script} && {pip_executable} install -r {requirements_file}"  
    print(f"Running command: {command}")  

    subprocess.run(command, shell=True, check=True, executable="/bin/bash")  

def check_installed_packages(venv_dir):  
    activate_script = os.path.join(venv_dir, 'bin', 'activate')  
    pip_executable = os.path.join(venv_dir, 'bin', 'pip')  

    # Construct and run the command to list installed packages  
    command = f"source {activate_script} && {pip_executable} list"  
    print(f"Checking installed packages: {command}")  

    subprocess.run(command, shell=True, check=True, executable="/bin/bash")  

def run_broker_script(venv_dir):  
    activate_script = os.path.join(venv_dir, 'bin', 'activate')  
    python_executable = os.path.join(venv_dir, 'bin', 'python')  

    broker_script = os.path.join(os.path.dirname(__file__), 'app/brokerv4.py')  
    if not os.path.exists(broker_script):  
        raise FileNotFoundError(f"The broker script `{broker_script}` does not exist.")  

    # Construct and run the command to activate the virtual environment and run broker.py  
    command = f"source {activate_script} && {python_executable} {broker_script}"  
    print(f"Running command: {command}")  

    subprocess.run(command, shell=True, check=True, executable="/bin/bash")  

def main():  
    venv_dir = create_virtualenv()  
    modify_permissions(venv_dir)  
    set_rw_permissions(constants.STORAGE_DIR)  
    set_rw_permissions(constants.EVENTS_DB_PATH)  
    activate_and_install_requirements(venv_dir)  
    check_installed_packages(venv_dir)  
    run_broker_script(venv_dir)  

if __name__ == "__main__":  
    main()