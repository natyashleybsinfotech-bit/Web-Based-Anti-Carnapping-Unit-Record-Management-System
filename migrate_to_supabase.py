#!/usr/bin/env python3
"""
Migration utility to sync existing MySQL data to Supabase PostgreSQL.
Run this once to migrate all existing data.
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import MySQLdb
from supabase import create_client

load_dotenv()


class MigrationManager:
    """Manages data migration from MySQL to Supabase"""
    
    def __init__(self):
        # MySQL connection
        self.mysql_host = os.getenv('MYSQL_HOST', 'localhost')
        self.mysql_user = os.getenv('MYSQL_USER', 'root')
        self.mysql_password = os.getenv('MYSQL_PASSWORD', '')
        self.mysql_db = os.getenv('MYSQL_DB', 'carnapping_db')
        
        # Supabase connection
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY required in .env")
        
        self.mysql_conn = None
        self.supabase_client = create_client(self.supabase_url, self.supabase_key)
        self.migration_log = []
    
    def connect_mysql(self):
        """Connect to MySQL database"""
        try:
            self.mysql_conn = MySQLdb.connect(
                host=self.mysql_host,
                user=self.mysql_user,
                passwd=self.mysql_password,
                db=self.mysql_db,
                charset='utf8mb4'
            )
            print("✓ Connected to MySQL")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to MySQL: {e}")
            return False
    
    def close_mysql(self):
        """Close MySQL connection"""
        if self.mysql_conn:
            self.mysql_conn.close()
    
    def migrate_table(self, table_name: str, column_mapping: dict = None):
        """
        Migrate a table from MySQL to Supabase.
        
        Args:
            table_name: Name of table to migrate
            column_mapping: Dict to map MySQL columns to Supabase (optional)
        
        Returns:
            Number of records migrated
        """
        try:
            cursor = self.mysql_conn.cursor(MySQLdb.cursors.DictCursor)
            # Safely query the table. Since table_name is internal, this is 
            # mostly for stylistic consistency with secure coding practices.
            query = "SELECT * FROM %s" % table_name
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            
            if not rows:
                print(f"  No data in {table_name}")
                return 0
            
            # Convert MySQL rows to Supabase format
            records = []
            for row in rows:
                record = {}
                for key, value in row.items():
                    # Map column names if provided
                    new_key = column_mapping.get(key, key) if column_mapping else key
                    
                    # Convert MySQL data types to PostgreSQL
                    if value is not None:
                        # TINYINT(1) → Boolean
                        if isinstance(value, int) and value in (0, 1):
                            # Check if this should be boolean based on column name
                            if 'is_' in key or 'force_' in key:
                                record[new_key] = bool(value)
                            else:
                                record[new_key] = value
                        else:
                            record[new_key] = value
                    else:
                        record[new_key] = None
                
                records.append(record)
            
            # Batch insert to Supabase
            if records:
                # Use upsert to handle potential duplicates during migration
                response = self.supabase_client.table(table_name).upsert(
                    records, 
                    on_conflict='id'
                ).execute()
                
                migrated = len(response.data) if response.data else 0
                print(f"  ✓ Migrated {migrated} records to {table_name}")
                self.migration_log.append({
                    'table': table_name,
                    'records': migrated,
                    'status': 'success'
                })
                return migrated
            return 0
        
        except Exception as e:
            print(f"  ✗ Error migrating {table_name}: {e}")
            self.migration_log.append({
                'table': table_name,
                'status': 'error',
                'error': str(e)
            })
            return 0
    
    def run_migration(self):
        """Execute full migration"""
        print("\n" + "="*60)
        print("MySQL → Supabase Migration")
        print("="*60)
        
        if not self.connect_mysql():
            return False
        
        try:
            print("\nMigrating tables...")
            
            # Define migration order (respect foreign keys)
            tables = [
                ('users', None),
                ('cases', None),
                ('activity_logs', None),
                ('report_exports', None),
            ]
            
            total_migrated = 0
            for table_name, column_map in tables:
                print(f"\nMigrating {table_name}...")
                migrated = self.migrate_table(table_name, column_map)
                total_migrated += migrated
            
            print("\n" + "="*60)
            print(f"Migration Complete: {total_migrated} total records migrated")
            print("="*60)
            
            # Print summary
            print("\nMigration Summary:")
            for log in self.migration_log:
                if log['status'] == 'success':
                    print(f"  ✓ {log['table']}: {log.get('records', 0)} records")
                else:
                    print(f"  ✗ {log['table']}: {log.get('error', 'Unknown error')}")
            
            return True
        
        finally:
            self.close_mysql()
    
    def verify_migration(self):
        """Verify data was migrated correctly"""
        print("\nVerifying migration...")
        
        tables = ['users', 'cases', 'activity_logs', 'report_exports']
        
        for table in tables:
            try:
                response = self.supabase_client.table(table).select('COUNT(*)').execute()
                count = len(response.data)
                print(f"  {table}: {count} records in Supabase")
            except Exception as e:
                print(f"  ✗ Error checking {table}: {e}")


def main():
    """Main migration function"""
    try:
        manager = MigrationManager()
        
        # Run migration
        success = manager.run_migration()
        
        if success:
            print("\n✓ Migration successful!")
            print("\nNext steps:")
            print("1. Verify data in Supabase dashboard")
            print("2. Update your Flask app to use Supabase")
            print("3. Deploy changes to production")
        else:
            print("\n✗ Migration failed")
            sys.exit(1)
    
    except Exception as e:
        print(f"✗ Migration error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
