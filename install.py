#!/usr/bin/env python3
"""
Script to install the most appropriate pre-compiled wheel file
for the current system, or build from source if no suitable wheel is found.
"""

import os
import sys
import json
import platform
import subprocess
from pathlib import Path
import argparse

def get_current_system_info():
    """Get basic information about the current system."""
    system_info = {
        "system": platform.system(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
    }
    
    # Get Linux distribution info if possible
    if platform.system() == "Linux":
        try:
            import distro
            system_info["distro_id"] = distro.id()
            system_info["distro_version"] = distro.version()
        except ImportError:
            try:
                # Try to get distribution info using lsb_release
                distro_id = subprocess.check_output(["lsb_release", "-si"], text=True).strip().lower()
                distro_version = subprocess.check_output(["lsb_release", "-sr"], text=True).strip()
                system_info["distro_id"] = distro_id
                system_info["distro_version"] = distro_version
            except:
                print("Warning: Could not determine Linux distribution.")
                system_info["distro_id"] = "linux"
                system_info["distro_version"] = ""
    
    return system_info

def find_best_wheel(system_info):
    """Find the best matching wheel file for the current system."""
    wheels_dir = Path("wheels")
    
    if not wheels_dir.exists() or not wheels_dir.is_dir():
        print("No wheels directory found.")
        return None
    
    # Map Python version to ABI tag
    py_version = "".join(system_info["python_version"].split(".")[:2])
    py_tag = f"cp{py_version}"
    
    # Create platform pattern
    if system_info["system"] == "Linux":
        distro_id = system_info.get("distro_id", "").lower()
        distro_version = system_info.get("distro_version", "")
        platform_pattern = f"{distro_id}{distro_version}-{system_info['machine']}"
        
        # Look for exact match first
        exact_match_dir = wheels_dir / platform_pattern
        if exact_match_dir.exists() and exact_match_dir.is_dir():
            # Look for matching Python version
            for wheel_file in exact_match_dir.glob(f"*{py_tag}*{py_tag}*.whl"):
                return wheel_file
            
            # If no matching Python version, get any wheel
            for wheel_file in exact_match_dir.glob("*.whl"):
                print(f"Warning: Found wheel with different Python version: {wheel_file.name}")
                return wheel_file
        
        # Try to find similar distribution
        for dir_path in wheels_dir.iterdir():
            if dir_path.is_dir() and distro_id in dir_path.name.lower():
                # Found similar distro, check for matching Python version
                for wheel_file in dir_path.glob(f"*{py_tag}*{py_tag}*.whl"):
                    print(f"Found wheel for similar platform: {dir_path.name}")
                    return wheel_file
                
                # If no matching Python version, get any wheel
                for wheel_file in dir_path.glob("*.whl"):
                    print(f"Warning: Found wheel for similar platform with different Python version: {wheel_file.name}")
                    return wheel_file
        
        # If no specific distro match, look for generic linux
        for dir_path in wheels_dir.iterdir():
            if dir_path.is_dir() and "linux" in dir_path.name.lower() and system_info["machine"] in dir_path.name:
                for wheel_file in dir_path.glob(f"*{py_tag}*{py_tag}*.whl"):
                    print(f"Found generic Linux wheel: {wheel_file.name}")
                    return wheel_file
    
    # For non-Linux or fallback
    for dir_path in wheels_dir.iterdir():
        if dir_path.is_dir() and system_info["system"].lower() in dir_path.name.lower() and system_info["machine"] in dir_path.name:
            for wheel_file in dir_path.glob("*.whl"):
                return wheel_file
    
    return None

def install_wheel(wheel_path, force=False, verbose=False):
    """Install the specified wheel file."""
    cmd = [sys.executable, "-m", "pip", "install"]
    
    if force:
        cmd.append("--force-reinstall")
    
    if verbose:
        cmd.append("-v")
    
    cmd.append(str(wheel_path))
    
    print(f"Installing wheel: {wheel_path}")
    subprocess.check_call(cmd)

def install_from_source(verbose=False):
    """Install package from source."""
    cmd = [sys.executable, "-m", "pip", "install", "."]
    
    if verbose:
        cmd.append("-v")
    
    print("No suitable wheel found. Installing from source...")
    subprocess.check_call(cmd)

def install_from_git(git_url, verbose=False):
    """Install package from git repository."""
    cmd = [sys.executable, "-m", "pip", "install", git_url]
    
    if verbose:
        cmd.append("-v")
    
    print(f"Installing from git: {git_url}")
    subprocess.check_call(cmd)

def main():
    parser = argparse.ArgumentParser(description="Install v-queue-python package")
    parser.add_argument("--force", action="store_true", help="Force reinstall")
    parser.add_argument("--source", action="store_true", help="Install from source even if wheel exists")
    parser.add_argument("--git", action="store_true", help="Install from git repository")
    parser.add_argument("--git-url", default="https://github.com/ваша-организация/v-queue-python.git", 
                        help="Git repository URL")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.git:
        install_from_git(args.git_url, verbose=args.verbose)
        return
    
    if not args.source:
        # Try to find suitable wheel
        system_info = get_current_system_info()
        if args.verbose:
            print("Current system info:")
            for key, value in system_info.items():
                print(f"  {key}: {value}")
        
        wheel_path = find_best_wheel(system_info)
        
        if wheel_path:
            # Found suitable wheel
            install_wheel(wheel_path, force=args.force, verbose=args.verbose)
            
            # Print platform info if available
            platform_info = wheel_path.parent / "platform-info.txt"
            if platform_info.exists():
                print("\nWheel platform information:")
                print(platform_info.read_text())
            
            return
    
    # No wheel found or source installation requested
    install_from_source(verbose=args.verbose)

if __name__ == "__main__":
    # Check if distro package is installed
    try:
        import distro
    except ImportError:
        # Only try to install distro if we're on Linux
        if platform.system() == "Linux":
            print("Installing required package: distro")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "distro"])
    
    main()
