"""Setup configuration for setuptools."""

import hashlib
import shutil
import subprocess
import tempfile
import zipfile
import stat
from pathlib import Path

from setuptools import setup
from wheel.bdist_wheel import bdist_wheel


class BdistWheelCommand(bdist_wheel):
    """Custom bdist_wheel that compiles nsjail and sets platform-specific tags."""

    def run(self):
        """Build nsjail binary before building the wheel."""
        project_root = Path(__file__).parent
        nsjail_dir = project_root / "nsjail"

        if not nsjail_dir.exists():
            raise RuntimeError(
                "nsjail submodule not found. "
                "Initialize with: git submodule update --init --recursive"
            )

        src_binary = nsjail_dir / "nsjail"
        if not src_binary.exists():
            print(f"Building nsjail in {nsjail_dir}...")
            subprocess.check_call(["make"], cwd=nsjail_dir)

        if not src_binary.exists():
            raise RuntimeError(f"nsjail build failed: {src_binary} not found")

        # Copy nsjail binary to package data directory
        pkg_data_dir = project_root / "src" / "nsjail" / "bin"
        pkg_data_dir.mkdir(parents=True, exist_ok=True)
        dest_binary = pkg_data_dir / "nsjail"
        shutil.copy(src_binary, dest_binary)
        dest_binary.chmod(0o755)
        print(f"Copied nsjail binary to {dest_binary}")

        # Build the wheel
        super().run()

        # Fix: Move all files from .data to root for correct auditwheel rpath
        # When Root-Is-Purelib: false, all files should be at root, not in .data
        dist_dir = Path(self.dist_dir or "dist")
        wheel_files = list(dist_dir.glob("*-py3-none-*.whl"))
        if not wheel_files:
            return

        wheel_file = wheel_files[0]
        print(f"Fixing wheel structure: {wheel_file.name}")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            extract_dir = tmpdir / "extract"
            extract_dir.mkdir()

            with zipfile.ZipFile(wheel_file, "r") as zf:
                zf.extractall(extract_dir)

            # Move everything from .data to root
            for data_dir in extract_dir.glob("*.data"):
                for category in ["purelib", "platlib"]:
                    cat_dir = data_dir / category
                    if cat_dir.exists():
                        for item in cat_dir.iterdir():
                            dest = extract_dir / item.name
                            if dest.exists():
                                if dest.is_dir():
                                    shutil.rmtree(dest)
                                else:
                                    dest.unlink()
                            shutil.move(str(item), str(dest))
                        # Remove empty category directory
                        if cat_dir.exists() and not list(cat_dir.iterdir()):
                            cat_dir.rmdir()
                # Remove empty .data directory
                if data_dir.exists() and not list(data_dir.iterdir()):
                    data_dir.rmdir()

            # Rebuild wheel with correct permissions and RECORD
            new_wheel = tmpdir / wheel_file.name
            record_entries = {}

            with zipfile.ZipFile(new_wheel, "w", zipfile.ZIP_DEFLATED) as zf:
                for file in sorted(extract_dir.rglob("*")):
                    if not file.is_file():
                        continue

                    arcname = str(file.relative_to(extract_dir))
                    with open(file, "rb") as f:
                        data = f.read()

                    # Set executable bit for binaries in bin/ directory
                    is_executable = "/bin/" in arcname or file.stat().st_mode & 0o111
                    unix_mode = 0o755 if is_executable else 0o644

                    zinfo = zipfile.ZipInfo(arcname)
                    zinfo.compress_type = zipfile.ZIP_DEFLATED
                    zinfo.external_attr = (unix_mode & 0xFFFF) << 16 | stat.S_IFREG

                    zf.writestr(zinfo, data)

                    # Skip RECORD file itself (will be added at the end)
                    if not arcname.endswith("/RECORD"):
                        digest = hashlib.sha256(data).hexdigest()
                        record_entries[arcname] = (
                            f"{arcname},sha256={digest},{len(data)}"
                        )

            # Add RECORD file
            record_path = None
            for path in sorted(extract_dir.glob("*.dist-info/RECORD")):
                record_path = str(path.relative_to(extract_dir))
                break

            if record_path:
                record_lines = sorted(record_entries.values())
                record_lines.append(f"{record_path},,")
                record_content = "\n".join(record_lines) + "\n"

                zinfo = zipfile.ZipInfo(record_path)
                zinfo.compress_type = zipfile.ZIP_DEFLATED
                zinfo.external_attr = (0o644 & 0xFFFF) << 16 | stat.S_IFREG
                with zipfile.ZipFile(new_wheel, "a", zipfile.ZIP_DEFLATED) as zf:
                    zf.writestr(zinfo, record_content)

            # Replace original wheel
            wheel_file.unlink()
            shutil.move(str(new_wheel), str(wheel_file))
            print("Moved all files to root - auditwheel will calculate correct rpath")

    def finalize_options(self):
        """Set wheel to be platform-specific but Python-agnostic."""
        super().finalize_options()
        self.root_is_pure = False

    def get_tag(self):
        """Return Python-agnostic but platform-specific wheel tags."""
        _, _, platform = super().get_tag()
        return "py3", "none", platform


if __name__ == "__main__":
    setup(cmdclass={"bdist_wheel": BdistWheelCommand})
