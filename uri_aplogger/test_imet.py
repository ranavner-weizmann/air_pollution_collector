#!/usr/bin/env python3
"""
Test iMet script independently
"""

import subprocess
import sys
import time

def test_imet():
    print("Testing iMet script...")
    
    try:
        # Run iMet script for 10 seconds
        process = subprocess.Popen(
            [sys.executable, "iMet_safe.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print("iMet process started, waiting 10 seconds...")
        time.sleep(10)
        
        # Try to terminate gracefully
        process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
        
        print(f"Return code: {process.returncode}")
        print(f"STDOUT:\n{stdout}")
        print(f"STDERR:\n{stderr}")
        
    except Exception as e:
        print(f"Error testing iMet: {e}")

if __name__ == "__main__":
    test_imet()
