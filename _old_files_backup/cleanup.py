#!/usr/bin/env python3
"""
Cleanup script to remove unused files and organize the project
"""

import os
import shutil
from pathlib import Path

def cleanup_project():
    """Remove unused files and organize the project"""
    
    # Files to remove
    files_to_remove = [
        # Backup files
        'app_backup_before_cleanup.py',
        'app_backup_indent.py', 
        'app_backup.py',
        'app_old_monolithic.py.bak',
        
        # Test files (can be moved to tests/ directory if needed)
        'debug_extraction.py',
        'test_extraction.py',
        'test_fix.py',
        'test_monthly_display.py',
        'test_monthly_issue.py',
        'test_new_chart.py',
        'test_profit_calculation.py',
        'test_validation.py',
        
        # Example files
        'app_with_auth_example.py',
        'example_dashboard_refactored.py',
        
        # Duplicate modular file (we have app_main.py now)
        'app_modular.py',
        
        # Unused modules (only used in old backups)
        'ai_chat_assistant.py',
        'ai_data_extractor.py',
        'comparative_analyzer.py',
        'gerenciador_arquivos.py',
        'verify_dashboard_totals.py',
        
        # Cleanup script itself
        'cleanup.py'
    ]
    
    # Directories to clean
    dirs_to_clean = [
        '__pycache__',
        '.pytest_cache',
        '.mypy_cache'
    ]
    
    print("🧹 Marine Seguros Project Cleanup")
    print("=" * 50)
    
    # Create backup directory
    backup_dir = Path('_old_files_backup')
    if not backup_dir.exists():
        backup_dir.mkdir()
        print(f"📁 Created backup directory: {backup_dir}")
    
    # Remove or backup files
    removed_count = 0
    for file in files_to_remove:
        if os.path.exists(file):
            try:
                # Move to backup instead of deleting
                shutil.move(file, backup_dir / file)
                print(f"📦 Moved to backup: {file}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Error moving {file}: {e}")
    
    # Clean Python cache directories
    cache_removed = 0
    for root, dirs, files in os.walk('.'):
        for dir_name in dirs_to_clean:
            if dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    shutil.rmtree(dir_path)
                    print(f"🗑️  Removed cache: {dir_path}")
                    cache_removed += 1
                except Exception as e:
                    print(f"❌ Error removing {dir_path}: {e}")
    
    # Clean .pyc files
    pyc_removed = 0
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    pyc_removed += 1
                except Exception as e:
                    print(f"❌ Error removing {file_path}: {e}")
    
    if pyc_removed > 0:
        print(f"🗑️  Removed {pyc_removed} .pyc files")
    
    print("\n📊 Cleanup Summary:")
    print(f"  • Files moved to backup: {removed_count}")
    print(f"  • Cache directories removed: {cache_removed}")
    print(f"  • .pyc files removed: {pyc_removed}")
    print(f"\n💡 Backup files are in: {backup_dir}")
    print("   You can safely delete this directory after reviewing.")
    
    # Show current structure
    print("\n📁 Clean Project Structure:")
    important_items = [
        'app.py (entry point)',
        'app_main.py (main application)',
        'core/ (business logic)',
        'ui/ (user interface)',
        'visualizations/ (charts)',
        'utils/ (utilities)',
        'data/ (database and files)',
        'static/ (static assets)',
        'database_manager.py',
        'requirements.txt',
        'README.md'
    ]
    
    for item in important_items:
        print(f"  ✓ {item}")


if __name__ == "__main__":
    import sys
    
    # Check for --yes flag to skip confirmation
    if '--yes' in sys.argv:
        cleanup_project()
        print("\n✅ Cleanup complete!")
    else:
        try:
            response = input("\n⚠️  This will move unused files to _old_files_backup/. Continue? (y/n): ")
            if response.lower() == 'y':
                cleanup_project()
                print("\n✅ Cleanup complete!")
            else:
                print("❌ Cleanup cancelled.")
        except EOFError:
            print("\n⚠️  Running in non-interactive mode. Use --yes flag to confirm.")
            print("Example: python cleanup.py --yes")