#!/usr/bin/env python3
"""
Script to find and fix job URL references in Django templates.

Usage:
    python fix_job_urls.py /path/to/templates/directory

This will:
1. Find all instances of {% url 'jobs:detail' job.id %}
2. Show you the files and line numbers
3. Optionally replace them with {% url 'jobs:detail' job.slug %}
"""

import os
import re
import sys
from pathlib import Path


def find_job_url_references(directory):
    """Find all job URL references in templates."""
    issues = []
    pattern = r"{%\s*url\s+['\"]jobs:detail['\"]\s+job\.id\s*%}"
    
    for root, dirs, files in os.walk(directory):
        # Skip hidden directories and common non-template directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
        
        for filename in files:
            if filename.endswith('.html'):
                filepath = os.path.join(root, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.split('\n')
                        
                        for line_num, line in enumerate(lines, 1):
                            if re.search(pattern, line):
                                issues.append({
                                    'file': filepath,
                                    'line': line_num,
                                    'content': line.strip()
                                })
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
    
    return issues


def fix_job_url_references(directory, dry_run=True):
    """Fix job URL references in templates."""
    pattern = r"{%\s*url\s+['\"]jobs:detail['\"]\s+job\.id\s*%}"
    replacement = "{% url 'jobs:detail' job.slug %}"
    
    fixed_files = []
    
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
        
        for filename in files:
            if filename.endswith('.html'):
                filepath = os.path.join(root, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check if file contains the pattern
                    if re.search(pattern, content):
                        new_content = re.sub(pattern, replacement, content)
                        
                        if not dry_run:
                            with open(filepath, 'w', encoding='utf-8') as f:
                                f.write(new_content)
                        
                        fixed_files.append(filepath)
                        
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")
    
    return fixed_files


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python fix_job_urls.py /path/to/templates/directory [--fix]")
        print("\nWithout --fix flag, it will only show what would be changed (dry run)")
        sys.exit(1)
    
    directory = sys.argv[1]
    do_fix = '--fix' in sys.argv
    
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a valid directory")
        sys.exit(1)
    
    print(f"Scanning directory: {directory}")
    print("=" * 70)
    
    # Find issues
    issues = find_job_url_references(directory)
    
    if not issues:
        print("\n✅ No issues found! All job URLs are using slugs.")
        return
    
    print(f"\n🔍 Found {len(issues)} issue(s):\n")
    
    for issue in issues:
        rel_path = os.path.relpath(issue['file'], directory)
        print(f"📄 {rel_path}:{issue['line']}")
        print(f"   {issue['content']}")
        print()
    
    if do_fix:
        print("\n🔧 Fixing issues...")
        fixed_files = fix_job_url_references(directory, dry_run=False)
        print(f"\n✅ Fixed {len(fixed_files)} file(s):")
        for filepath in fixed_files:
            rel_path = os.path.relpath(filepath, directory)
            print(f"   - {rel_path}")
    else:
        print("\n💡 To fix these issues, run:")
        print(f"   python {sys.argv[0]} {directory} --fix")
        print("\nThis will replace all instances of:")
        print("   {% url 'jobs:detail' job.id %}")
        print("with:")
        print("   {% url 'jobs:detail' job.slug %}")


if __name__ == '__main__':
    main()