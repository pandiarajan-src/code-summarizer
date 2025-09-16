#!/usr/bin/env python3
"""Comprehensive test script for the Code Summarizer API.

This script tests all API endpoints exposed by the Code Summarizer API:
- Health endpoints
- Analysis endpoints (all variants)
- Configuration endpoints
- File validation endpoints
"""

import argparse
import json
import shutil
import sys
import tempfile
import time
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any

import requests
from requests import Response


class APITester:
    """Comprehensive API testing class for Code Summarizer API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.session = requests.Session()
        self.results: dict[str, Any] = {}

    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp."""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def test_response(
        self, name: str, response: Response, expected_status: int = 200
    ) -> bool:
        """Test response and log results."""
        success = response.status_code == expected_status
        status_icon = "✅" if success else "❌"

        self.log(f"{status_icon} {name}")
        self.log(f"   Status: {response.status_code} (expected: {expected_status})")

        if not success:
            self.log(f"   Error: {response.text}", "ERROR")
        else:
            try:
                data = response.json()
                self.log(f"   Response keys: {list(data.keys())}")
            except (ValueError, TypeError, KeyError):
                self.log(f"   Response length: {len(response.text)} chars")

        self.results[name] = {
            "success": success,
            "status_code": response.status_code,
            "response_time": response.elapsed.total_seconds(),
        }

        return success

    def test_root_endpoint(self) -> bool:
        """Test root endpoint."""
        self.log("Testing root endpoint...")
        try:
            response = self.session.get(self.base_url)
            return self.test_response("Root endpoint", response)
        except Exception as e:
            self.log(f"❌ Root endpoint failed: {e}", "ERROR")
            return False

    def test_health_endpoints(self) -> bool:
        """Test all health-related endpoints."""
        self.log("Testing health endpoints...")
        success = True

        # Basic health check
        try:
            response = self.session.get(f"{self.api_base}/health")
            success &= self.test_response("Health check", response)
        except Exception as e:
            self.log(f"❌ Health check failed: {e}", "ERROR")
            success = False

        # Detailed health check
        try:
            response = self.session.get(f"{self.api_base}/health?detailed=true")
            success &= self.test_response("Detailed health check", response)
        except Exception as e:
            self.log(f"❌ Detailed health check failed: {e}", "ERROR")
            success = False

        # Version endpoint
        try:
            response = self.session.get(f"{self.api_base}/version")
            success &= self.test_response("Version endpoint", response)
        except Exception as e:
            self.log(f"❌ Version endpoint failed: {e}", "ERROR")
            success = False

        # Config endpoint
        try:
            response = self.session.get(f"{self.api_base}/config")
            success &= self.test_response("Config endpoint", response)
        except Exception as e:
            self.log(f"❌ Config endpoint failed: {e}", "ERROR")
            success = False

        # Info endpoint
        try:
            response = self.session.get(f"{self.api_base}/info")
            success &= self.test_response("Info endpoint", response)
        except Exception as e:
            self.log(f"❌ Info endpoint failed: {e}", "ERROR")
            success = False

        # Ping endpoint
        try:
            response = self.session.get(f"{self.api_base}/ping")
            success &= self.test_response("Ping endpoint", response)
        except Exception as e:
            self.log(f"❌ Ping endpoint failed: {e}", "ERROR")
            success = False

        return success

    def test_analysis_config_endpoints(self) -> bool:
        """Test analysis configuration endpoints."""
        self.log("Testing analysis configuration endpoints...")
        success = True

        # Get supported file types
        try:
            response = self.session.get(f"{self.api_base}/analyze/supported-types")
            success &= self.test_response("Supported file types", response)
        except Exception as e:
            self.log(f"❌ Supported file types failed: {e}", "ERROR")
            success = False

        # Get analysis config
        try:
            response = self.session.get(f"{self.api_base}/analyze/config")
            success &= self.test_response("Analysis config", response)
        except Exception as e:
            self.log(f"❌ Analysis config failed: {e}", "ERROR")
            success = False

        return success

    def create_sample_files(self) -> list[dict[str, Any]]:
        """Create sample code files for testing."""
        return [
            {
                "filename": "hello.py",
                "content": '''def hello_world():
    """A simple hello world function."""
    print("Hello, World!")
    return "Hello, World!"

if __name__ == "__main__":
    hello_world()
''',
                "file_type": ".py",
            },
            {
                "filename": "utils.js",
                "content": """/**
 * Utility functions for the application
 */

function formatString(str) {
    return str.trim().toLowerCase();
}

function calculateSum(a, b) {
    return a + b;
}

module.exports = {
    formatString,
    calculateSum
};
""",
                "file_type": ".js",
            },
        ]

    def create_sample_zip(self) -> bytes:
        """Create a sample ZIP file for testing."""
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Add Python file
            zip_file.writestr(
                "main.py",
                '''#!/usr/bin/env python3
"""Sample Python application."""

def main():
    print("Sample application")
    return 0

if __name__ == "__main__":
    main()
''',
            )
            # Add JavaScript file
            zip_file.writestr(
                "script.js",
                """// Sample JavaScript file
console.log("Hello from JavaScript!");

function greet(name) {
    return `Hello, ${name}!`;
}
""",
            )

        zip_buffer.seek(0)
        return zip_buffer.read()

    def test_file_validation(self) -> bool:
        """Test file validation endpoint."""
        self.log("Testing file validation...")
        success = True

        try:
            # Create sample files
            files = []
            for file_data in self.create_sample_files():
                files.append(
                    (
                        "files",
                        (file_data["filename"], file_data["content"], "text/plain"),
                    )
                )

            response = self.session.post(
                f"{self.api_base}/analyze/validate", files=files
            )
            success &= self.test_response("File validation", response)

        except Exception as e:
            self.log(f"❌ File validation failed: {e}", "ERROR")
            success = False

        return success

    def test_basic_analysis(self) -> bool:
        """Test basic file analysis endpoint."""
        self.log("Testing basic analysis...")
        success = True

        try:
            payload = {
                "files": self.create_sample_files(),
                "output_format": "json",
                "verbose": True,
            }

            response = self.session.post(f"{self.api_base}/analyze", json=payload)
            success &= self.test_response("Basic analysis", response)

        except Exception as e:
            self.log(f"❌ Basic analysis failed: {e}", "ERROR")
            success = False

        return success

    def test_upload_analysis(self) -> bool:
        """Test file upload analysis endpoint."""
        self.log("Testing upload analysis...")
        success = True

        try:
            # Test with individual files
            files = []
            for file_data in self.create_sample_files():
                files.append(
                    (
                        "files",
                        (file_data["filename"], file_data["content"], "text/plain"),
                    )
                )

            data = {
                "output_format": "json",
                "verbose": "true",
                "extract_archives": "true",
            }

            response = self.session.post(
                f"{self.api_base}/analyze/upload", files=files, data=data
            )
            success &= self.test_response("Upload analysis", response)

        except Exception as e:
            self.log(f"❌ Upload analysis failed: {e}", "ERROR")
            success = False

        # Test with ZIP file
        try:
            zip_data = self.create_sample_zip()
            files = [("files", ("sample.zip", zip_data, "application/zip"))]
            data = {
                "output_format": "json",
                "verbose": "true",
                "extract_archives": "true",
            }

            response = self.session.post(
                f"{self.api_base}/analyze/upload", files=files, data=data
            )
            success &= self.test_response("ZIP upload analysis", response)

        except Exception as e:
            self.log(f"❌ ZIP upload analysis failed: {e}", "ERROR")
            success = False

        return success

    def test_batch_analysis(self) -> bool:
        """Test batch analysis endpoints."""
        self.log("Testing batch analysis...")
        success = True

        # Test batch analysis via JSON
        try:
            payload = {
                "files": self.create_sample_files(),
                "output_format": "json",
                "verbose": True,
                "force_batch": True,
            }

            response = self.session.post(f"{self.api_base}/analyze/batch", json=payload)
            success &= self.test_response("Batch analysis", response)

        except Exception as e:
            self.log(f"❌ Batch analysis failed: {e}", "ERROR")
            success = False

        # Test batch analysis via upload
        try:
            files = []
            for file_data in self.create_sample_files():
                files.append(
                    (
                        "files",
                        (file_data["filename"], file_data["content"], "text/plain"),
                    )
                )

            data = {"output_format": "json", "verbose": "true", "force_batch": "true"}

            response = self.session.post(
                f"{self.api_base}/analyze/batch/upload", files=files, data=data
            )
            success &= self.test_response("Batch upload analysis", response)

        except Exception as e:
            self.log(f"❌ Batch upload analysis failed: {e}", "ERROR")
            success = False

        return success

    def test_path_analysis(self) -> bool:
        """Test path-based analysis endpoint."""
        self.log("Testing path analysis...")

        # Create temporary files for testing
        with tempfile.TemporaryDirectory() as tmpdirname:
            temp_dir = Path(tmpdirname)
            temp_dir.mkdir(exist_ok=True)

            try:
                # Create sample files
                (temp_dir / "test.py").write_text(
                    """def test():
        print("Test function")
        return True
    """
                )
                (temp_dir / "test.js").write_text(
                    """function test() {
        console.log("Test function");
        return true;
    }
    """
                )

                payload = {
                    "paths": [str(temp_dir)],
                    "output_format": "json",
                    "verbose": True,
                    "recursive": True,
                }

                response = self.session.post(
                    f"{self.api_base}/analyze/paths", json=payload
                )
                success = self.test_response("Path analysis", response)

            except Exception as e:
                self.log(f"❌ Path analysis failed: {e}", "ERROR")
                success = False
            finally:
                # Cleanup
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)

            return success

    def test_error_handling(self) -> bool:
        """Test error handling scenarios."""
        self.log("Testing error handling...")
        success = True

        # Test with empty files
        try:
            payload = {"files": [], "output_format": "json"}
            response = self.session.post(f"{self.api_base}/analyze", json=payload)
            # FastAPI returns 422 for validation errors (empty files array fails min_items=1)
            success &= self.test_response("Empty files error", response, 422)

        except Exception as e:
            self.log(f"❌ Empty files error test failed: {e}", "ERROR")
            success = False

        # Test with invalid JSON config overrides
        try:
            files = []
            for file_data in self.create_sample_files()[:1]:  # Just one file
                files.append(
                    (
                        "files",
                        (file_data["filename"], file_data["content"], "text/plain"),
                    )
                )

            data = {"config_overrides": "invalid json", "output_format": "json"}

            response = self.session.post(
                f"{self.api_base}/analyze/upload", files=files, data=data
            )
            success &= self.test_response("Invalid config error", response, 422)

        except Exception as e:
            self.log(f"❌ Invalid config error test failed: {e}", "ERROR")
            success = False

        # Test non-existent path
        try:
            payload = {"paths": ["/non/existent/path"], "output_format": "json"}

            response = self.session.post(f"{self.api_base}/analyze/paths", json=payload)
            # This should return an error status
            success &= self.test_response("Non-existent path error", response, 400)

        except Exception as e:
            self.log(f"❌ Non-existent path error test failed: {e}", "ERROR")
            success = False

        return success

    def test_different_output_formats(self) -> bool:
        """Test different output formats."""
        self.log("Testing different output formats...")
        success = True

        formats = ["json", "markdown", "both"]

        for output_format in formats:
            try:
                payload = {
                    "files": self.create_sample_files()[:1],  # Just one file for speed
                    "output_format": output_format,
                    "verbose": False,
                }

                response = self.session.post(f"{self.api_base}/analyze", json=payload)
                success &= self.test_response(
                    f"Output format: {output_format}", response
                )

            except Exception as e:
                self.log(f"❌ Output format {output_format} failed: {e}", "ERROR")
                success = False

        return success

    def test_config_overrides(self) -> bool:
        """Test configuration overrides."""
        self.log("Testing configuration overrides...")
        success = True

        try:
            config_overrides = {"llm": {"temperature": 0.0, "max_tokens": 2000}}

            payload = {
                "files": self.create_sample_files()[:1],
                "output_format": "json",
                "config_overrides": config_overrides,
            }

            response = self.session.post(f"{self.api_base}/analyze", json=payload)
            success &= self.test_response("Config overrides", response)

        except Exception as e:
            self.log(f"❌ Config overrides failed: {e}", "ERROR")
            success = False

        return success

    def run_all_tests(self) -> dict[str, Any]:
        """Run all tests and return comprehensive results."""
        self.log("🚀 Starting comprehensive API testing...")
        start_time = time.time()

        test_results = {
            "root_endpoint": self.test_root_endpoint(),
            "health_endpoints": self.test_health_endpoints(),
            "analysis_config": self.test_analysis_config_endpoints(),
            "file_validation": self.test_file_validation(),
            "basic_analysis": self.test_basic_analysis(),
            "upload_analysis": self.test_upload_analysis(),
            "batch_analysis": self.test_batch_analysis(),
            "path_analysis": self.test_path_analysis(),
            "error_handling": self.test_error_handling(),
            "output_formats": self.test_different_output_formats(),
            "config_overrides": self.test_config_overrides(),
        }

        total_time = time.time() - start_time

        # Calculate statistics
        if self.results and isinstance(list(self.results.values())[0], dict):
            total_tests = len(
                [v for test_group in self.results.values() for v in test_group]
            )
        else:
            total_tests = len(self.results)
        passed_tests = sum(
            1 for result in self.results.values() if result.get("success", False)
        )

        summary = {
            "total_test_groups": len(test_results),
            "passed_test_groups": sum(test_results.values()),
            "total_individual_tests": total_tests,
            "passed_individual_tests": passed_tests,
            "success_rate": (
                (passed_tests / total_tests * 100) if total_tests > 0 else 0
            ),
            "total_time_seconds": total_time,
            "test_results": test_results,
            "individual_results": self.results,
        }

        return summary

    def print_summary(self, summary: dict[str, Any]):
        """Print test summary."""
        self.log("=" * 60)
        self.log("🏁 TEST SUMMARY")
        self.log("=" * 60)

        self.log(f"Total test groups: {summary['total_test_groups']}")
        self.log(f"Passed test groups: {summary['passed_test_groups']}")
        self.log(f"Total individual tests: {summary['total_individual_tests']}")
        self.log(f"Passed individual tests: {summary['passed_individual_tests']}")
        self.log(f"Success rate: {summary['success_rate']:.1f}%")
        self.log(f"Total time: {summary['total_time_seconds']:.2f}s")

        self.log("\nTest Group Results:")
        for test_name, passed in summary["test_results"].items():
            icon = "✅" if passed else "❌"
            self.log(f"  {icon} {test_name.replace('_', ' ').title()}")

        if summary["success_rate"] == 100:
            self.log("\n🎉 All tests passed! API is working correctly.")
        else:
            failed_groups = summary["total_test_groups"] - summary["passed_test_groups"]
            self.log(f"\n⚠️  {failed_groups} test group(s) failed.")
            self.log("Check the logs above for detailed error information.")


def main():
    """Main testing function."""
    parser = argparse.ArgumentParser(
        description="Comprehensive API testing for Code Summarizer"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL for the API (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--save-results",
        action="store_true",
        help="Save detailed results to a JSON file",
    )
    parser.add_argument(
        "--test-group",
        choices=["health", "analysis", "upload", "batch", "all"],
        default="all",
        help="Run specific test group (default: all)",
    )

    args = parser.parse_args()

    # Check if API is running
    try:
        requests.get(args.url, timeout=5)
        print(f"✅ API is responding at {args.url}")
    except requests.exceptions.RequestException as e:
        print(f"❌ API is not responding at {args.url}")
        print(f"Error: {e}")
        print("\nMake sure the API server is running:")
        print(
            "  PYTHONPATH=src uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
        )
        sys.exit(1)

    # Run tests
    tester = APITester(args.url)

    if args.test_group == "all":
        summary = tester.run_all_tests()
    else:
        # Run specific test group
        test_methods = {
            "health": tester.test_health_endpoints,
            "analysis": tester.test_basic_analysis,
            "upload": tester.test_upload_analysis,
            "batch": tester.test_batch_analysis,
        }

        if args.test_group in test_methods:
            result = test_methods[args.test_group]()
            summary = {
                "total_test_groups": 1,
                "passed_test_groups": 1 if result else 0,
                "success_rate": 100 if result else 0,
                "test_results": {args.test_group: result},
            }
        else:
            print(f"Unknown test group: {args.test_group}")
            sys.exit(1)

    tester.print_summary(summary)

    # Save results if requested
    if args.save_results:
        filename = f"api_test_results_{int(time.time())}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(f"\n📄 Detailed results saved to: {filename}")

    # Exit with appropriate code
    sys.exit(0 if summary["success_rate"] == 100 else 1)


if __name__ == "__main__":
    main()
