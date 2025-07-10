#!/usr/bin/env python3
"""
Reset test data to initial state
Quick utility to reset pantry data between manual tests
"""

import subprocess
import sys
import os

def reset_data():
    """Reset pantry to demo state"""
    print("🔄 Resetting test data to initial state...")
    
    try:
        # Run setup_demo_data.py
        script_path = os.path.join(
            os.path.dirname(__file__), 
            "../../backend_gateway/scripts/setup_demo_data.py"
        )
        
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Test data reset successfully!")
            print("\nDemo pantry items restored:")
            print("- Pasta (Spaghetti): 453.592g")
            print("- Pasta (Penne): 453.592g") 
            print("- Milk (Whole): 946.353ml")
            print("- Eggs: 12 each")
            print("- All Purpose Flour: 907.185g")
            print("- Butter (Unsalted): 453.592g")
            print("- Sugar (Granulated): 907.185g")
            print("- Salt: 737.09g")
            print("- Tomato: 4 each")
            print("- And more...")
        else:
            print(f"❌ Failed to reset test data")
            print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
        
    return True

if __name__ == "__main__":
    reset_data()