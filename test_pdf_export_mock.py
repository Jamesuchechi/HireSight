#!/usr/bin/env python
"""
Mock test for PDF export functionality without database dependency.
"""
import os
import sys
import django
from unittest.mock import Mock, MagicMock
from io import BytesIO

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hiresight.settings')
django.setup()

from apps.screening.pdf_export import ScreeningPDFExporter


def test_pdf_generation_with_mock_data():
    """Test PDF generation with mock session and results."""
    print("Testing PDF generation with mock data...")
    
    try:
        # Create mock session
        mock_session = Mock()
        mock_session.id = '12345'
        mock_session.title = 'Senior Software Engineer Screening'
        mock_session.job = Mock(title='Senior Software Engineer')
        mock_session.company = Mock(name='Acme Corp')
        mock_session.criteria = Mock(required_skills=['Python', 'Django', 'PostgreSQL'])
        
        # Create mock results
        mock_results = []
        for i in range(1, 6):
            mock_result = Mock()
            mock_result.id = str(i)
            mock_result.match_score = 90 - (i * 5)
            mock_result.is_shortlisted = i <= 3
            mock_result.resume = Mock()
            mock_result.resume.user = Mock()
            mock_result.resume.user.get_full_name = Mock(return_value=f'Candidate {i}')
            mock_result.resume.user.email = f'candidate{i}@example.com'
            mock_result.match_details = {
                'skills_match': {
                    'matched': ['Python', 'Django'] if i <= 3 else ['Python'],
                    'missing': [] if i <= 3 else ['Django', 'PostgreSQL']
                },
                'experience_match': {'years': 5 + i},
                'education_match': {'degree': 'BS Computer Science'}
            }
            mock_results.append(mock_result)
        
        mock_session.results = Mock()
        mock_session.results.filter = Mock(return_value=mock_results)
        mock_session.results.count = Mock(return_value=len(mock_results))
        mock_session.results.aggregate = Mock(return_value={'match_score__avg': 70.0})
        mock_session.results.first = Mock(return_value=mock_results[0])
        mock_session.results.__iter__ = Mock(return_value=iter(mock_results))
        
        # Create exporter
        print("  Creating PDF exporter...")
        exporter = ScreeningPDFExporter(mock_session, results=mock_results)
        
        # Generate PDF
        print("  Generating PDF...")
        pdf_buffer = exporter.generate()
        
        # Verify output
        pdf_content = pdf_buffer.getvalue()
        pdf_size = len(pdf_content)
        
        # Check if it's a valid PDF (starts with %PDF)
        is_valid_pdf = pdf_content.startswith(b'%PDF')
        
        if is_valid_pdf and pdf_size > 1000:
            print(f"✅ PDF generated successfully!")
            print(f"   File size: {pdf_size:,} bytes")
            print(f"   Valid PDF: {is_valid_pdf}")
            
            # Save to file for verification
            output_path = '/tmp/mock_screening_report.pdf'
            with open(output_path, 'wb') as f:
                f.write(pdf_content)
            
            print(f"📄 Mock PDF saved to: {output_path}")
            return True
        else:
            print(f"❌ PDF validation failed!")
            print(f"   Starts with %PDF: {is_valid_pdf}")
            print(f"   Size > 1000 bytes: {pdf_size > 1000}")
            return False
    
    except Exception as e:
        print(f"❌ Error generating PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_pdf_exporter_initialization():
    """Test PDF exporter initialization."""
    print("Testing PDF exporter initialization...")
    
    try:
        # Create minimal mock session
        mock_session = Mock()
        mock_session.id = 'test-123'
        mock_session.title = 'Test Session'
        mock_session.job = None
        mock_session.company = Mock(name='Test Company')
        
        # Initialize exporter with empty results list
        exporter = ScreeningPDFExporter(mock_session, results=[])
        
        # Check that exporter was initialized
        has_buffer = hasattr(exporter, 'buffer')
        has_styles = hasattr(exporter, 'styles')
        has_results = hasattr(exporter, 'results')
        
        if has_buffer and has_styles and has_results:
            print("✅ PDF exporter initialized correctly!")
            print(f"   Buffer: {type(exporter.buffer).__name__}")
            print(f"   Styles: {type(exporter.styles).__name__}")
            print(f"   Results: {type(exporter.results).__name__}")
            return True
        else:
            print("❌ PDF exporter missing required attributes!")
            return False
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def test_pdf_with_empty_results():
    """Test PDF generation with empty results."""
    print("Testing PDF generation with empty results...")
    
    try:
        mock_session = Mock()
        mock_session.id = 'empty-session'
        mock_session.title = 'Empty Session'
        mock_session.job = None
        mock_session.company = Mock(name='Test Co')
        mock_session.criteria = None
        
        exporter = ScreeningPDFExporter(mock_session, results=[])
        pdf_buffer = exporter.generate()
        
        pdf_size = len(pdf_buffer.getvalue())
        if pdf_size > 0:
            print(f"✅ Empty PDF generated successfully!")
            print(f"   File size: {pdf_size:,} bytes")
            return True
        else:
            print(f"❌ Generated PDF is empty!")
            return False
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("Mock PDF Export Test Suite")
    print("=" * 60)
    
    results = []
    results.append(("PDF Exporter Initialization", test_pdf_exporter_initialization()))
    results.append(("PDF with Empty Results", test_pdf_with_empty_results()))
    results.append(("PDF with Mock Data", test_pdf_generation_with_mock_data()))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(passed for _, passed in results)
    print("\n" + ("🎉 All tests passed!" if all_passed else "⚠️  Some tests failed"))
    sys.exit(0 if all_passed else 1)
