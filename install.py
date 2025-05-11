#!/usr/bin/env python3
"""
Installation script for the Searchable PDF Library.
This script helps users install the library and its dependencies.
"""

import os
import sys
import subprocess
import argparse
import shutil
import re
import tempfile
from pathlib import Path

def run_command(cmd, description, exit_on_error=False, capture_output=True):
    """Run a command and handle errors appropriately."""
    print(f"{description}...")
    try:
        if capture_output:
            result = subprocess.run(
                cmd, 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            print(f"{description} completed successfully.")
        else:
            # For commands where we want to show output in real-time
            result = subprocess.run(cmd, check=True)
            print(f"{description} completed successfully.")
        return True, result
    except subprocess.CalledProcessError as e:
        print(f"Error: {description} failed.")
        print(f"Exit code: {e.returncode}")
        if capture_output:
            print("Output:")
            print(e.stdout)
            print("Error:")
            print(e.stderr)
        if exit_on_error:
            sys.exit(1)
        return False, e
    except Exception as e:
        print(f"Unexpected error during {description.lower()}: {str(e)}")
        if exit_on_error:
            sys.exit(1)
        return False, e

def check_venv():
    """Check if running in a virtual environment."""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def get_python_version(python_executable):
    """Get the Python version as a tuple (major, minor)."""
    try:
        result = subprocess.run(
            [python_executable, "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        version_str = result.stdout.strip()
        major, minor = map(int, version_str.split('.'))
        return major, minor
    except Exception as e:
        print(f"Error getting Python version: {e}")
        return None

def create_compatible_requirements(python_version, skip_packages=None):
    """Create a compatible requirements file based on Python version."""
    if skip_packages is None:
        skip_packages = []
    
    temp_requirements = []
    
    with open("requirements.txt", "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                temp_requirements.append(line)
                continue
            
            # Check if this package should be skipped
            package_name = re.split(r'[=<>]', line)[0].strip()
            if package_name in skip_packages:
                temp_requirements.append(f"# Skipped: {line}")
                continue
            
            # Add version constraints for problematic packages
            if python_version and python_version[0] >= 3 and python_version[1] >= 12:
                # Python 3.12+ compatibility adjustments
                if package_name == "spacy":
                    temp_requirements.append("# spacy with blis is not compatible with Python 3.12+")
                    temp_requirements.append("# Using a minimal spacy installation")
                    temp_requirements.append("spacy>=3.7.2,<3.8.0 --no-deps")
                    temp_requirements.append("wasabi>=1.1.2,<1.2.0")
                    temp_requirements.append("srsly>=2.4.8,<2.5.0")
                    temp_requirements.append("catalogue>=2.0.9,<2.1.0")
                    temp_requirements.append("spacy-legacy>=3.0.12,<3.1.0")
                    temp_requirements.append("spacy-loggers>=1.0.5,<1.1.0")
                    temp_requirements.append("murmurhash>=1.0.10,<1.1.0")
                    temp_requirements.append("tqdm>=4.65.0")
                    temp_requirements.append("smart-open>=6.4.0")
                    temp_requirements.append("typer>=0.9.0")
                    temp_requirements.append("pydantic>=2.0.0,<3.0.0")
                    continue
                elif package_name in ["blis", "thinc", "cymem", "preshed", "pandas"]:
                    # Skip packages known to have compatibility issues with Python 3.12+
                    temp_requirements.append(f"# Skipped: {line} (not compatible with Python 3.12+)")
                    continue
            
            # Add the original line
            temp_requirements.append(line)
    
    # Write the temporary requirements file
    temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt')
    temp_file.write('\n'.join(temp_requirements))
    temp_file.close()
    
    return temp_file.name

def main():
    """Run the installation script."""
    parser = argparse.ArgumentParser(description="Install the Searchable PDF Library")
    parser.add_argument("--dev", action="store_true", help="Install development dependencies")
    parser.add_argument("--no-venv", action="store_true", help="Skip virtual environment creation (not recommended)")
    parser.add_argument("--venv-path", type=str, default=".venv", help="Path for the virtual environment")
    parser.add_argument("--spacy-model", action="store_true", help="Install spaCy language model")
    parser.add_argument("--upgrade-pip", action="store_true", help="Upgrade pip before installation")
    parser.add_argument("--sequential", action="store_true", help="Install packages one by one")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    parser.add_argument("--skip-problematic", action="store_true", help="Skip problematic packages like spacy and blis")
    parser.add_argument("--minimal", action="store_true", help="Install minimal dependencies for basic functionality")
    parser.add_argument("--super-minimal", action="store_true", help="Install only the most essential dependencies, skipping all problematic packages")
    args = parser.parse_args()
    
    # Change to the script's directory
    os.chdir(Path(__file__).parent)
    
    # Check if we're already in a virtual environment
    in_venv = check_venv()
    
    if in_venv and not args.no_venv:
        print("Already running in a virtual environment.")
        python = sys.executable
    elif not args.no_venv:
        # Create a virtual environment
        venv_path = Path(args.venv_path)
        if venv_path.exists():
            print(f"Virtual environment at {venv_path} already exists.")
        else:
            print(f"Creating virtual environment at {venv_path}...")
            try:
                subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
                print("Virtual environment created successfully.")
            except subprocess.CalledProcessError:
                print("Error creating virtual environment with venv module.")
                print("Trying with virtualenv instead...")
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", "virtualenv"], check=True)
                    subprocess.run([sys.executable, "-m", "virtualenv", str(venv_path)], check=True)
                    print("Virtual environment created with virtualenv.")
                except subprocess.CalledProcessError:
                    print("Failed to create virtual environment. Please create one manually.")
                    print("Example: python -m venv .venv")
                    print("Then activate it and run this script again.")
                    sys.exit(1)
        
        # Determine the Python executable to use
        if os.name == "nt":  # Windows
            python = str(venv_path / "Scripts" / "python")
            activate_script = str(venv_path / "Scripts" / "activate")
        else:  # Unix/Linux/Mac
            python = str(venv_path / "bin" / "python")
            activate_script = str(venv_path / "bin" / "activate")
        
        # Check if the virtual environment Python exists
        if not Path(python).exists():
            print(f"Error: Python executable not found at {python}")
            print("Virtual environment may be corrupted. Please delete it and try again.")
            sys.exit(1)
            
        print("\nVirtual environment is ready.")
        print(f"To activate it manually, run: source {activate_script} (Unix/Mac) or {activate_script} (Windows)")
        print("Continuing installation in the virtual environment...\n")
    else:
        # User explicitly requested to skip virtual environment
        print("WARNING: Installing without a virtual environment is not recommended.")
        print("This may lead to conflicts with system packages or permission issues.")
        python = sys.executable
    
    # Always upgrade pip, setuptools, and wheel first
    run_command(
        [python, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"],
        "Upgrading pip, setuptools, and wheel"
    )
    
    # Get Python version
    python_version = get_python_version(python)
    print(f"Python version: {python_version[0]}.{python_version[1]}")
    
    # Determine which packages to skip
    skip_packages = []
    if args.skip_problematic or python_version[0] >= 3 and python_version[1] >= 12:
        skip_packages = ["blis", "thinc", "cymem", "preshed"]
        if python_version[0] >= 3 and python_version[1] >= 13:
            # Additional packages to skip for Python 3.13+
            skip_packages.extend(["pandas", "numpy"])
        if args.minimal:
            skip_packages.extend(["spacy", "nltk", "pytesseract"])
    
    # Determine which requirements file to use
    if args.super_minimal and os.path.exists("minimal_requirements.txt"):
        requirements_file = "minimal_requirements.txt"
        print(f"Using super minimal requirements file: {requirements_file}")
    else:
        # Create a compatible requirements file
        requirements_file = create_compatible_requirements(python_version, skip_packages)
        print(f"Created compatible requirements file: {requirements_file}")
    
    # Install dependencies
    if args.sequential:
        print("Installing dependencies one by one...")
        with open(requirements_file, "r") as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        
        failed_packages = []
        for package in requirements:
            success, _ = run_command(
                [python, "-m", "pip", "install", package, "--prefer-binary"],
                f"Installing {package}",
                exit_on_error=False,
                capture_output=not args.verbose
            )
            if not success:
                failed_packages.append(package)
        
        if failed_packages:
            print("\nThe following packages failed to install:")
            for package in failed_packages:
                print(f"  - {package}")
            print("\nYou may need to install system dependencies or resolve conflicts.")
            print("Try installing these packages manually or check for system requirements.")
        else:
            print("All dependencies installed successfully.")
    else:
        # Install all dependencies at once
        success, _ = run_command(
            [python, "-m", "pip", "install", "-r", requirements_file, "--prefer-binary"],
            "Installing dependencies",
            exit_on_error=False,
            capture_output=not args.verbose
        )
        if not success:
            print("\nTry running with --sequential to identify problematic packages:")
            print(f"  {python} {__file__} --sequential")
            print("\nOr try with --skip-problematic to skip packages known to cause issues:")
            print(f"  {python} {__file__} --skip-problematic")
            if not args.verbose:
                print("\nRun with --verbose for more detailed error information.")
    
    # Clean up temporary requirements file
    try:
        os.unlink(requirements_file)
    except:
        pass
    
    # Install development dependencies if requested
    if args.dev:
        print("Installing development dependencies...")
        dev_requirements = [
            "pytest==7.4.3",
            "pytest-cov==4.1.0",
            "black==23.11.0",
            "isort==5.12.0",
            "flake8==6.1.0",
            "mypy==1.7.0",
            "sphinx==7.2.6",
            "sphinx-rtd-theme==1.3.0"
        ]
        success, _ = run_command(
            [python, "-m", "pip", "install"] + dev_requirements + ["--prefer-binary"],
            "Installing development dependencies",
            exit_on_error=False,
            capture_output=not args.verbose
        )
        if not success:
            print("Failed to install some development dependencies. Continuing...")
    
    # Install spaCy language model if requested
    if args.spacy_model and "spacy" not in skip_packages:
        success, _ = run_command(
            [python, "-m", "spacy", "download", "en_core_web_sm"],
            "Installing spaCy language model",
            exit_on_error=False,
            capture_output=not args.verbose
        )
        if not success:
            print("Failed to install spaCy language model. You can install it manually later.")
    
    # Install the library in development mode
    success, _ = run_command(
        [python, "-m", "pip", "install", "-e", "."],
        "Installing the library in development mode",
        exit_on_error=False,
        capture_output=not args.verbose
    )
    if not success:
        print("Failed to install the library in development mode.")
        print("You may need to resolve dependency issues first.")
        return
    
    print()
    print("Installation complete!")
    print()
    
    # Determine activation command for the virtual environment
    if not args.no_venv and not in_venv:
        if os.name == "nt":  # Windows
            activate_cmd = f"{args.venv_path}\\Scripts\\activate"
        else:  # Unix/Linux/Mac
            activate_cmd = f"source {args.venv_path}/bin/activate"
        
        print(f"To activate the virtual environment, run:")
        print(f"  {activate_cmd}")
        print()
        
        # Create a convenience script to activate and run quickstart
        if os.name == "nt":  # Windows
            with open("run_quickstart.bat", "w") as f:
                f.write(f"@echo off\n")
                f.write(f"call {args.venv_path}\\Scripts\\activate\n")
                f.write(f"python quickstart.py\n")
            print("A convenience script has been created: run_quickstart.bat")
        else:  # Unix/Linux/Mac
            with open("run_quickstart.sh", "w") as f:
                f.write(f"#!/bin/bash\n")
                f.write(f"source {args.venv_path}/bin/activate\n")
                f.write(f"python quickstart.py\n")
            os.chmod("run_quickstart.sh", 0o755)  # Make executable
            print("A convenience script has been created: run_quickstart.sh")
    
    print("To get started, run:")
    if not args.no_venv and not in_venv:
        if os.name == "nt":  # Windows
            print("  run_quickstart.bat")
        else:  # Unix/Linux/Mac
            print("  ./run_quickstart.sh")
    else:
        print("  python quickstart.py")
    print()
    
    print("For more information, see the README.md file.")
    
    # Print troubleshooting information
    print("\nTroubleshooting:")
    print("  If you encounter issues with dependencies, try:")
    print(f"  - {python} {__file__} --sequential  (to install packages one by one)")
    print(f"  - {python} {__file__} --skip-problematic  (to skip problematic packages)")
    print(f"  - {python} {__file__} --minimal  (to install minimal dependencies)")
    print(f"  - {python} {__file__} --verbose  (for detailed error output)")
    print("  - Check system requirements for packages like pytesseract (may need Tesseract OCR installed)")
    print("\nSystem-specific notes:")
    print("  - macOS: Some packages may require Homebrew: brew install tesseract")
    print("  - Linux: You may need to install development libraries: apt-get install python3-dev")
    print("  - Windows: Ensure you have the Visual C++ Build Tools installed for some packages")
    
    if skip_packages:
        print("\nNote: The following packages were skipped during installation:")
        for package in skip_packages:
            print(f"  - {package}")
        print("Some functionality may be limited. You can try installing these packages manually if needed.")

if __name__ == "__main__":
    main()
