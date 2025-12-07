#!/usr/bin/env python3

"""
Flask Online Shop - Quick Start Script
Run this script to start the online shop application.
"""

import os
import sys

PORT=5002

def main():
    print("=" * 60)
    print("FLASK ONLINE SHOP - STARTING APPLICATION")
    print("=" * 60)
    print()
    print("🏪 Starting Flask Online Shop...")
    print("📊 Initializing database with sample data...")
    print("🔐 Creating admin and customer accounts...")
    print()
    print("Default Accounts:")
    print("  Admin: admin / admin123")
    print("  Customer: customer / customer123")
    print()
    print("🌐 Application will be available at:")
    print(f"  Frontend Store: http://localhost:{PORT}")
    print(f"  Admin Panel: http://localhost:{PORT}/admin")
    print()
    print("Press Ctrl+C to stop the application")
    print("=" * 60)
    print()

    # Import and run the Flask app
    try:
        from online_shop import app
        app.run(debug=True, host='0.0.0.0', port=PORT)
    except ImportError:
        print("❌ Error: Could not import the Flask application.")
        print("Make sure you have installed all requirements:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
