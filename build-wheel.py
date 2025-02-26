#!/usr/bin/env python3
"""
Script to build wheel files with platform-specific metadata.
Automatically detects current environment and creates appropriate metadata files.
"""

import os
import sys
import json
import shutil
import platform
import subprocess
import datetime
import glob
from pathlib import Path

def get_system_info():
    """Get detailed information about the current system."""
    
    # Get basic platform info
    system_info = {
        "platform": {
            "system": platform.system(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "architecture": platform.architecture()[0],
        },
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
            "compiler": platform.python_compiler(),
        },
        "build_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Linux-specific info
    if platform.system() == "Linux":
        try:
            import distro
            system_info["platform"]["distribution"] = distro.name(pretty=True)
            system_info["platform"]["distro_id"] = distro.id()
            system_info["platform"]["distro_version"] = distro.version()
            system_info["platform"]["distro_codename"] = distro.codename()
        except Exception as e:
            print(f"Warning: Failed to get Linux distribution info: {e}")
    
    # Get glibc version on Linux
    if platform.system() == "Linux":
        try:
            glibc_version = subprocess.check_output("ldd --version | head -n 1", 
                                                   shell=True, text=True)
            if "glibc" in glibc_version.lower():
                # Extract version number
                parts = glibc_version.split()
                for part in parts:
                    if part[0].isdigit():
                        system_info["platform"]["glibc_version"] = part
                        break
        except Exception as e:
            print(f"Warning: Failed to get glibc version: {e}")
    
    # Get libstdc++ version if possible
    if platform.system() == "Linux":
        try:
            gcc_version = subprocess.check_output("gcc --version | head -n 1", 
                                                shell=True, text=True)
            system_info["platform"]["gcc_version"] = gcc_version.strip()
        except Exception as e:
            print(f"Warning: Failed to get GCC version: {e}")
    
    # Get Rust info
    try:
        rust_version = subprocess.check_output("rustc --version", 
                                             shell=True, text=True)
        system_info["rust"] = rust_version.strip()
    except Exception as e:
        print(f"Warning: Failed to get Rust version: {e}")
        system_info["rust"] = "unknown"
    
    return system_info

def create_platform_dirname(system_info):
    """Create a directory name based on platform information."""
    if platform.system() == "Linux":
        distro_id = system_info["platform"].get("distro_id", "linux").lower()
        distro_version = system_info["platform"].get("distro_version", "")
        arch = system_info["platform"]["machine"]
        
        # Format: ubuntu22.04-x86_64
        return f"{distro_id}{distro_version}-{arch}"
    else:
        # For non-Linux platforms
        system = system_info["platform"]["system"].lower()
        machine = system_info["platform"]["machine"]
        return f"{system}-{machine}"

def clean_build_files():
    """Clean temporary build files."""
    print("Cleaning up temporary build files...")
    
    # Clean dist directory
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    
    # Clean build directory
    if os.path.exists("build"):
        shutil.rmtree("build")
    
    # Clean egg-info directories
    for egg_info in glob.glob("*.egg-info") + glob.glob("src/*.egg-info"):
        if os.path.isdir(egg_info):
            print(f"Removing {egg_info}")
            shutil.rmtree(egg_info)
    
    # Clean __pycache__ directories
    for pycache in glob.glob("**/__pycache__", recursive=True):
        if os.path.isdir(pycache):
            print(f"Removing {pycache}")
            shutil.rmtree(pycache)
    
    # Clean .pyc files
    for pyc in glob.glob("**/*.pyc", recursive=True):
        if os.path.isfile(pyc):
            print(f"Removing {pyc}")
            os.remove(pyc)

def build_wheel():
    """Build the wheel file and create metadata."""
    print("Building wheel file...")
    
    # Ensure dist directory is clean
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    
    # Build the wheel
    subprocess.check_call([sys.executable, "setup.py", "bdist_wheel"])
    
    # Get system information
    system_info = get_system_info()
    
    # Get the wheel file
    wheel_file = list(Path("dist").glob("*.whl"))
    if not wheel_file:
        print("No wheel file found in dist directory!")
        return
    
    wheel_file = wheel_file[0]
    wheel_filename = wheel_file.name
    
    # Create platform-specific directory name
    platform_dir = create_platform_dirname(system_info)
    
    # Create wheels directory structure
    wheels_dir = Path("wheels") / platform_dir
    wheels_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy wheel file to platform directory
    dest_wheel = wheels_dir / wheel_filename
    shutil.copy(wheel_file, dest_wheel)
    
    # Create metadata file
    metadata = {
        "wheel_file": wheel_filename,
        "system_info": system_info
    }
    
    metadata_file = wheels_dir / f"{wheel_filename[:-4]}.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)
    
    # Create a simple platform info text file for human reading
    platform_info = [
        f"Wheel file: {wheel_filename}",
        f"Build date: {system_info['build_date']}",
        f"System: {system_info['platform']['system']}",
        f"Architecture: {system_info['platform']['machine']} ({system_info['platform']['architecture']})"
    ]
    
    # Add Linux distribution info if available
    if platform.system() == "Linux" and "distribution" in system_info["platform"]:
        platform_info.append(f"Distribution: {system_info['platform']['distribution']}")
        if "distro_version" in system_info["platform"]:
            platform_info.append(f"Version: {system_info['platform']['distro_version']}")
        if "distro_codename" in system_info["platform"]:
            platform_info.append(f"Codename: {system_info['platform']['distro_codename']}")
    
    platform_info.append(f"Python: {system_info['python']['implementation']} {system_info['python']['version']}")
    platform_info.append(f"Rust: {system_info['rust']}")
    
    # Extra info for Linux
    if platform.system() == "Linux":
        if "glibc_version" in system_info["platform"]:
            platform_info.append(f"glibc: {system_info['platform']['glibc_version']}")
        if "gcc_version" in system_info["platform"]:
            platform_info.append(f"GCC: {system_info['platform']['gcc_version']}")
    
    with open(wheels_dir / "platform-info.txt", "w") as f:
        f.write("\n".join(platform_info))
    
    print(f"\nWheel build complete!")
    print(f"Wheel file: {dest_wheel}")
    print(f"Metadata: {metadata_file}")
    print(f"Platform info: {wheels_dir / 'platform-info.txt'}")
    print(f"\nTo install this wheel, run:")
    print(f"pip install {dest_wheel}")
    
    # Clean up temporary build files
    clean_build_files()

if __name__ == "__main__":
    # Make sure the distro package is installed
    try:
        import distro
    except ImportError:
        print("Installing required package: distro")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "distro"])
        import distro
    
    build_wheel()
