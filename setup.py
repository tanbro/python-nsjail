"""Setup configuration for setuptools."""

import shutil
import subprocess
from pathlib import Path

from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext as _build_ext


class NsjailExtension(Extension):
    """Extension that builds nsjail binary (not a real C extension)."""

    def __init__(self):
        # Empty C source to satisfy setuptools extension build
        super().__init__(
            "nsjail._ext",
            sources=["src/nsjail/_stub.c"],
        )


class BuildExtCommand(_build_ext):
    """Custom build_ext that compiles nsjail binary."""

    def build_extension(self, ext):
        """Build nsjail binary and stub extension."""
        # Compile the stub extension (creates .so file)
        super().build_extension(ext)

        # Now compile and copy nsjail binary
        project_root = Path(__file__).parent
        nsjail_dir = project_root / "nsjail"
        src_binary = nsjail_dir / "nsjail"

        if not nsjail_dir.exists():
            raise RuntimeError(
                "nsjail submodule not found. "
                "Initialize with: git submodule update --init --recursive"
            )

        # Skip compilation if binary already exists
        if not src_binary.exists():
            print(f"Building nsjail in {nsjail_dir}...")
            subprocess.check_call(["make"], cwd=nsjail_dir)

        if not src_binary.exists():
            raise RuntimeError(f"nsjail build failed: {src_binary} not found")

        # Copy nsjail binary alongside the .so file
        dest_dir = Path(self.get_ext_fullpath(ext.name)).parent
        dest_binary = dest_dir / "nsjail"
        shutil.copy(src_binary, dest_binary)
        dest_binary.chmod(0o755)
        print(f"Copied nsjail binary to {dest_binary}")

        # Also copy to src/nsjail/ for editable installs
        src_pkg_dir = project_root / "src" / "nsjail"
        src_pkg_dir.mkdir(parents=True, exist_ok=True)
        src_binary = src_pkg_dir / "nsjail"
        shutil.copy(nsjail_dir / "nsjail", src_binary)
        src_binary.chmod(0o755)
        print(f"Also copied to {src_binary} for editable installs")


if __name__ == "__main__":
    setup(
        ext_modules=[NsjailExtension()],
        cmdclass={"build_ext": BuildExtCommand},
    )
