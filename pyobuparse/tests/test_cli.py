import unittest
from unittest import mock
import subprocess
import os
import sys
import tempfile

# Add pyobuparse/src to sys.path to allow importing pyobuparse directly
# This is similar to how test_parser.py handles imports
_PYOBUPARSE_SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if _PYOBUPARSE_SRC_DIR not in sys.path:
    sys.path.insert(0, _PYOBUPARSE_SRC_DIR)

from pyobuparse import cli # Should now be importable

# Minimal IVF file content:
# Header: DKIF, version 0, headerlen 32, AV01, 1x1 resolution, 30/1 fps, 1 frame.
# Frame 1 Hdr: size 2 (for TD OBU), PTS 0
# Frame 1 Data: Temporal Delimiter OBU (0x12 0x00)
MINIMAL_IVF_CONTENT = (
    b'DKIF'  # Signature
    b'\x00\x00'  # Version
    b'\x20\x00'  # Header Length (32)
    b'AV01'  # FourCC
    b'\x01\x00'  # Width (1)
    b'\x01\x00'  # Height (1)
    b'\x1e\x00\x00\x00'  # Framerate Numerator (30)
    b'\x01\x00\x00\x00'  # Framerate Denominator (1)
    b'\x01\x00\x00\x00'  # Frame Count (1)
    b'\x00\x00\x00\x00'  # Unused
    # Frame 1
    b'\x02\x00\x00\x00'  # Frame Size (2 bytes)
    b'\x00\x00\x00\x00\x00\x00\x00\x00'  # PTS (0)
    b'\x12\x00'  # OBU: Temporal Delimiter (type 2, size 0)
)

class TestCli(unittest.TestCase):

    def setUp(self):
        # Create a temporary IVF file
        self.temp_ivf_file = tempfile.NamedTemporaryFile(delete=False, suffix=".ivf")
        self.temp_ivf_file.write(MINIMAL_IVF_CONTENT)
        self.temp_ivf_file.close()
        self.temp_ivf_filename = self.temp_ivf_file.name

    def tearDown(self):
        os.remove(self.temp_ivf_filename)

    def run_obudump_command(self, args_list):
        """Helper to run obudump and return stdout, stderr, and exit code."""
        # Construct the command. Assumes obudump is installed or we can call it via python -m module
        # For testing local changes without installation, it's often easier to run the cli.py script directly.
        # However, the task implies testing the installed script "obudump".
        # If "obudump" is not in PATH during test, this will fail.
        # A more robust way for uninstalled packages is to run:
        # [sys.executable, "-m", "pyobuparse.cli"] + args_list
        # For now, let's try to directly call cli.main() by patching sys.argv
        
        # To test the script as if it's run from command line:
        # We can use subprocess, but need to ensure the environment can find pyobuparse
        # or call the script directly with python interpreter.
        
        # Simplest for now: patch sys.argv and call cli.main directly
        # This tests the logic within cli.main but not the script wrapper generation by setuptools.
        
        full_args = ["obudump_placeholder"] + args_list # "obudump_placeholder" is for argv[0]
        
        # Patch sys.argv
        with mock.patch.object(sys, 'argv', full_args):
            # Capture stdout and stderr
            with mock.patch('sys.stdout', new_callable=unittest.mock.StringIO) as mock_stdout:
                with mock.patch('sys.stderr', new_callable=unittest.mock.StringIO) as mock_stderr:
                    exit_code = 0
                    try:
                        cli.main()
                    except SystemExit as e:
                        exit_code = e.code if isinstance(e.code, int) else 1 # Ensure int
                    return mock_stdout.getvalue(), mock_stderr.getvalue(), exit_code

    def test_basic_output(self):
        """Test basic output with the minimal IVF file."""
        stdout, stderr, exit_code = self.run_obudump_command([self.temp_ivf_filename])
        
        self.assertEqual(exit_code, 0)
        # Check stderr for IVF header info (printed by cli.py)
        self.assertIn("IVF Header: Version=0", stderr)
        self.assertIn("Codec=b'AV01'", stderr)
        self.assertIn("Frames=1", stderr)
        
        # Check stdout for OBU info
        self.assertIn("IVF Frame 1: Size=2, PTS=0", stdout)
        self.assertIn("OBU: Type=OBP_OBU_TEMPORAL_DELIMITER", stdout)
        self.assertIn("Size=0", stdout) # TD OBU payload is 0
        self.assertIn("Processed 1 frames", stderr)

    def test_verbose_output(self):
        """Test verbose output with the minimal IVF file."""
        stdout, stderr, exit_code = self.run_obudump_command(["--verbose", self.temp_ivf_filename])
        
        self.assertEqual(exit_code, 0)
        self.assertIn("IVF Header: Version=0", stderr)
        self.assertIn("Codec=b'AV01'", stderr)
        
        self.assertIn("IVF Frame 1: Size=2, PTS=0", stdout)
        self.assertIn("OBU: Type=OBP_OBU_TEMPORAL_DELIMITER", stdout)
        # For TD, verbose doesn't add much as it has no specific parser, but check basic structure
        self.assertIn("Size=0", stdout) 
        self.assertIn("Processed 1 frames", stderr)

    def test_file_not_found(self):
        """Test CLI behavior when the input file is not found."""
        stdout, stderr, exit_code = self.run_obudump_command(["non_existent_file.ivf"])
        
        self.assertNotEqual(exit_code, 0) # Should exit with an error
        self.assertIn("Error: File not found: non_existent_file.ivf", stderr)

    def test_max_obus_arg(self):
        """Test the --max-obus argument."""
        # Create an IVF with more than one OBU in a frame
        # Frame 1: TD (2 bytes: 0x12 0x00), Padding (3 bytes: 0x7A 0x01 0x00)
        # Frame Size = 2 + 3 = 5
        multi_obu_ivf_content = (
            b'DKIF' b'\x00\x00' b'\x20\x00' b'AV01'
            b'\x01\x00' b'\x01\x00' b'\x1e\x00\x00\x00' b'\x01\x00\x00\x00'
            b'\x01\x00\x00\x00' b'\x00\x00\x00\x00'
            b'\x05\x00\x00\x00'  # Frame Size (5 bytes)
            b'\x00\x00\x00\x00\x00\x00\x00\x00'  # PTS (0)
            b'\x12\x00'          # OBU: Temporal Delimiter (type 2, size 0)
            b'\x7a\x01\x00'      # OBU: Padding (type 15, size 1, payload 0x00)
        )
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ivf") as tmp_f:
            tmp_f.write(multi_obu_ivf_content)
            tmp_f_name = tmp_f.name
        
        try:
            stdout, _, exit_code = self.run_obudump_command(["--max-obus", "1", tmp_f_name])
            self.assertEqual(exit_code, 0)
            self.assertIn("OBU: Type=OBP_OBU_TEMPORAL_DELIMITER", stdout)
            self.assertIn("... (further OBUs in frame 1 truncated due to --max-obus)", stdout)
            self.assertNotIn("Type=OBP_OBU_PADDING", stdout) # The second OBU should not be printed
        finally:
            os.remove(tmp_f_name)

if __name__ == "__main__":
    unittest.main()
