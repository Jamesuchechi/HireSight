#!/usr/bin/env python
"""
Test script for PDF export functionality.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hiresight.settings')
django.setup()

from apps.screening.models import ScreeningSession, ScreeningResult
from apps.screening.pdf_export import ScreeningPDFExporter
from django.contrib.auth import get_user_model

User = get_user_model()


def test_pdf_generation():
    """Test PDF generation with sample data."""
    print("Testing PDF export functionality...")
    
    # Find a screening session with results
    session = ScreeningSession.objects.filter(
        results__isnull=False
    ).first()
    
    if not session:
        print("❌ No screening sessions with results found.")
        print("Please create a screening session and add some results first.")
        return False
    
    try:
        # Generate PDF
        print(f"📋 Generating PDF for session: {session.title}")
        print(f"   Results count: {session.results.count()}")
        
        exporter = ScreeningPDFExporter(session)
        pdf_buffer = exporter.generate()
        
        # Check output
        pdf_size = len(pdf_buffer.getvalue())
        print(f"✅ PDF generated successfully!")
        print(f"   File size: {pdf_size:,} bytes")
        
        # Save to file for manual verification
        output_path = '/tmp/test_screening_report.pdf'
        with open(output_path, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        print(f"📄 Test PDF saved to: {output_path}")
        print("   You can now open this file in a PDF reader to verify output.")
        
        return True
    
    except Exception as e:
        print(f"❌ Error generating PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_pdf_with_multiple_results():
    """Test PDF generation with larger result sets."""
    print("\nTesting PDF with multiple results...")
    
    session = ScreeningSession.objects.filter(
        results__isnull=False
    ).annotate(
        result_count=django.db.models.Count('results')
    ).filter(result_count__gte=10).first()
    
    if not session:
        print("⚠️  No sessions with 10+ results found. Skipping this test.")
        return True
    
    try:
        print(f"📋 Generating PDF for: {session.title}")
        print(f"   Processing {session.results.count()} results...")
        
        exporter = ScreeningPDFExporter(session)
        pdf_buffer = exporter.generate()
        
        pdf_size = len(pdf_buffer.getvalue())
        print(f"✅ Large PDF generated successfully!")
        print(f"   File size: {pdf_size:,} bytes")
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("PDF Export Test Suite")
    print("=" * 60)
    
    results = []
    results.append(("Basic PDF Generation", test_pdf_generation()))
    results.append(("Large Result Set", test_pdf_with_multiple_results()))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(passed for _, passed in results)
    sys.exit(0 if all_passed else 1)
