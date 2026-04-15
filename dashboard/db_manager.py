#!/usr/bin/env python3
"""
Database Management Utility
Commands: init, seed, clear, backup, info
"""

import sys
import os
from datetime import datetime
import json
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from database import db, Metric, Activity, ChartData, User, seed_initial_data


def init_database():
    """Initialize the database tables"""
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully")
        print(f"📍 Database location: {app.config['SQLALCHEMY_DATABASE_URI']}")


def seed_database():
    """Seed the database with initial data"""
    with app.app_context():
        if Metric.query.count() > 0:
            response = input("⚠️  Database already has data. Clear and reseed? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Seeding cancelled")
                return
            clear_database(confirm=False)
        
        seed_initial_data()
        print("✅ Database seeded with initial data")


def clear_database(confirm=True):
    """Clear all data from database"""
    if confirm:
        response = input("⚠️  This will delete ALL data. Are you sure? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Operation cancelled")
            return
    
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("✅ Database cleared")


def backup_database():
    """Create a backup of the database"""
    db_path = 'dashboard.db'
    if not os.path.exists(db_path):
        print("❌ No database file found")
        return
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'dashboard_backup_{timestamp}.db'
    
    shutil.copy2(db_path, backup_path)
    print(f"✅ Database backed up to: {backup_path}")


def show_info():
    """Show database information"""
    with app.app_context():
        print("\n" + "=" * 60)
        print("📊 DATABASE INFORMATION")
        print("=" * 60)
        
        print(f"\n📍 Location: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        print("\n📈 Table Statistics:")
        print(f"   Metrics:    {Metric.query.count()} records")
        print(f"   Activities: {Activity.query.count()} records")
        print(f"   Chart Data: {ChartData.query.count()} records")
        print(f"   Users:      {User.query.count()} records")
        
        print("\n💾 Current Metrics:")
        metrics = Metric.query.all()
        for metric in metrics:
            print(f"   {metric.name}: {metric.value} {metric.unit}")
        
        print("\n👥 Users:")
        users = User.query.all()
        for user in users:
            status = "✅ Active" if user.is_active else "❌ Inactive"
            print(f"   {user.username} ({user.email}) - {status}")
        
        print("\n📝 Recent Activities:")
        activities = Activity.query.order_by(Activity.timestamp.desc()).limit(5).all()
        for activity in activities:
            print(f"   {activity.time} - {activity.user}: {activity.action} ({activity.status})")
        
        print("\n" + "=" * 60)


def export_data():
    """Export database data to JSON"""
    with app.app_context():
        data = {
            'metrics': [m.to_dict() for m in Metric.query.all()],
            'activities': [a.to_dict() for a in Activity.query.all()],
            'chart_data': [c.to_dict() for c in ChartData.query.all()],
            'users': [u.to_dict() for u in User.query.all()]
        }
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'database_export_{timestamp}.json'
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Data exported to: {filename}")


def show_help():
    """Show help message"""
    print("""
Database Management Utility
============================

Commands:
  init     - Initialize database tables
  seed     - Seed database with initial data
  clear    - Clear all data from database
  backup   - Create a backup of the database
  export   - Export data to JSON file
  info     - Show database information
  help     - Show this help message

Usage:
  python db_manager.py <command>

Examples:
  python db_manager.py init
  python db_manager.py seed
  python db_manager.py info
    """)


def main():
    """Main function"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    commands = {
        'init': init_database,
        'seed': seed_database,
        'clear': clear_database,
        'backup': backup_database,
        'export': export_data,
        'info': show_info,
        'help': show_help
    }
    
    if command in commands:
        print("\n🔧 Database Manager")
        print("=" * 60)
        commands[command]()
        print("=" * 60 + "\n")
    else:
        print(f"❌ Unknown command: {command}")
        show_help()


if __name__ == '__main__':
    main()
