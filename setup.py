"""Setup configuration for setuptools."""

import platform
import re
import shutil
import subprocess
from pathlib import Path

from setuptools import Extension, setup
from setuptools.command.bdist_wheel import bdist_wheel
from setuptools.command.build import build as _build
from setuptools.command.build_ext import build_ext as _build_ext


class NsjailExtension(Extension):
    """Fake extension to trick setuptools into using platlib layout."""

    def __init__(self):
        # This extension is never actually built
        super().__init__("nsjail._fake_ext", sources=[])


class BuildExtCommand(_build_ext):
    """Custom build_ext that does nothing (our extension is fake)."""

    def run(self):
        """Skip the entire build_ext process for our fake extension."""
        # Don't call super().run() - this skips all extension building
        # This is needed for editable installs to work
        pass

    def build_extension(self, ext):
        """Skip building the fake extension."""
        pass

    def get_outputs(self):
        """Return empty list since we don't build any actual extensions."""
        return []

    def get_source_files(self):
        """Return empty list since we don't have any source files."""
        return []


class BuildCommand(_build):
    """Custom build command that compiles nsjail binary."""

    def run(self):
        """Compile nsjail and copy to src/nsjail/bin/ before building."""
        project_root = Path(__file__).parent.resolve()
        nsjail_dir = project_root / "nsjail"
        src_binary = nsjail_dir / "nsjail"

        if not nsjail_dir.exists():
            raise RuntimeError(
                f"nsjail submodule not found at {nsjail_dir}. "
                "Initialize with: git submodule update --init --recursive"
            )

        print(f"Building nsjail in {nsjail_dir}...")
        subprocess.run(["make"], cwd=nsjail_dir, check=True)

        if not src_binary.exists():
            raise RuntimeError(f"nsjail build failed: {src_binary} not found")

        pkg_dir = project_root / "src" / "nsjail"
        pkg_dir.mkdir(exist_ok=True)
        dest_binary = pkg_dir / "nsjail"
        shutil.copy(src_binary, dest_binary)
        dest_binary.chmod(0o755)
        print(f"Copied nsjail binary to {dest_binary}")

        super().run()


class BdistWheelCommand(bdist_wheel):
    """Custom bdist_wheel to set py3-none tag."""

    def finalize_options(self):
        super().finalize_options()

        # nsjail is Linux-only
        if platform.system().lower() != "linux":
            raise RuntimeError(f"nsjail is Linux-only, building on {platform.system()}")

        # Use generic linux platform tag, auditwheel will fix it to manylinux/musllinux
        self.plat_name = f"linux_{platform.machine().lower()}"
        print(f"Platform: {self.plat_name}")

    def write_wheelfile(self, wheelfile_base: str, generator: str | None = None):
        """Write WHEEL file with py3-none tag."""
        # nsjail is Linux-only
        if (plat_name := platform.system().lower()) != "linux":
            raise RuntimeError(f"nsjail is Linux-only, building on {platform.system()}")

        if generator:
            super().write_wheelfile(wheelfile_base, generator)
        else:
            super().write_wheelfile(wheelfile_base)

        wheel_path = Path(wheelfile_base)
        if wheel_path.is_dir():
            wheel_path = wheel_path / "WHEEL"
        if wheel_path.exists() and wheel_path.is_file():
            content = wheel_path.read_text()
            content = re.sub(
                rf"Tag: cp[0-9]+-cp[0-9]+-({plat_name}_[a-z0-9_]+)",
                r"Tag: py3-none-\1",
                content,
            )
            wheel_path.write_text(content)
            print("Modified WHEEL file to use py3-none tag")


if __name__ == "__main__":
    setup(
        ext_modules=[NsjailExtension()],
        cmdclass={
            "build": BuildCommand,
            "build_ext": BuildExtCommand,
            "bdist_wheel": BdistWheelCommand,
        },
    )
