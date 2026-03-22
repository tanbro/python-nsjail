"""Setup configuration for setuptools."""

import hashlib
import platform
import zipfile
from pathlib import Path

from setuptools import setup
from setuptools.command.bdist_wheel import bdist_wheel


class BdistWheelCommand(bdist_wheel):
    """Custom bdist_wheel to add nsjail binary to scripts."""

    def finalize_options(self):
        """Set platform-specific options."""
        super().finalize_options()
        self.plat_name = f"{platform.system().lower()}_{platform.machine().lower()}"
        self.root_is_pure = False
        print(f"Platform: {self.plat_name}")

    def run(self):
        """Build wheel and inject nsjail binary into scripts."""
        if platform.system() != "Linux":
            raise RuntimeError(f"nsjail is Linux-only, building on {platform.system()}")

        # Build the standard wheel first
        super().run()

        # Find the wheel that was just created
        if not self.dist_dir:
            raise RuntimeError("`dist_dir` is not set")
        dist_dir = Path(self.dist_dir)
        wheels = list(dist_dir.glob("nsjail-*.whl"))
        if not wheels:
            raise FileNotFoundError(f"No wheel found in {dist_dir}")

        wheel_path = wheels[-1]
        print(f"Injecting nsjail binary into: {wheel_path}")

        # Get nsjail binary source
        project_root = Path(__file__).parent.resolve()
        src_binary = project_root / "nsjail" / "nsjail"

        if not src_binary.exists():
            raise FileNotFoundError(
                f"nsjail binary not found at {src_binary}. "
                "Build first: cd nsjail && make"
            )

        # Modify the wheel to add the binary
        data_dir = f"{self.distribution.get_name()}-{self.distribution.get_version()}.data/scripts"
        binary_dest = f"{data_dir}/nsjail"

        # Read binary content
        binary_data = src_binary.read_bytes()

        # Create new wheel with injected binary
        new_wheel_path = wheel_path.with_suffix(".tmp.whl")
        record_entries = []
        record_name = None
        wheel_name = None

        with zipfile.ZipFile(wheel_path, "r") as old_zip:
            # Find dist-info directory
            for name in old_zip.namelist():
                if name.endswith("RECORD"):
                    record_name = name
                elif name.endswith("WHEEL"):
                    wheel_name = name

            with zipfile.ZipFile(
                new_wheel_path, "w", compression=zipfile.ZIP_DEFLATED
            ) as new_zip:
                # Copy all files except RECORD and WHEEL
                for info in old_zip.infolist():
                    if info.filename.endswith("RECORD") or info.filename.endswith(
                        "WHEEL"
                    ):
                        continue
                    data = old_zip.read(info.filename)
                    record_entries.append((info.filename, data))
                    new_zip.writestr(info, data)

                # Add the nsjail binary
                binary_info = zipfile.ZipInfo(binary_dest)
                binary_info.external_attr = (
                    0o100755 << 16
                )  # -rwxr-xr-x (regular file + 0755)
                binary_info.compress_type = zipfile.ZIP_DEFLATED
                new_zip.writestr(binary_info, binary_data)
                record_entries.append((binary_dest, binary_data))

                # Write updated RECORD
                if record_name:
                    record_lines = []
                    for name, data in record_entries:
                        digest = hashlib.sha256(data).hexdigest()
                        size = len(data)
                        record_lines.append(f"{name},sha256={digest},{size}")
                    record_content = "\n".join(record_lines) + "\n"
                    new_zip.writestr(record_name, record_content)

                # Write updated WHEEL
                if wheel_name:
                    wheel_content = old_zip.read(wheel_name).decode()
                    # Replace Python tag and ABI tag - handle any cp3xx/py3xx version
                    import re

                    # Match patterns like: Tag: cp312-cp312-linux_x86_64 or cp39-cp39-linux_aarch64
                    new_wheel_content = re.sub(
                        r"Tag: cp[0-9]+-cp[0-9]+-(linux_[a-z0-9_]+)",
                        r"Tag: py3-none-\1",
                        wheel_content,
                    )
                    # Also replace the py3x/py3x in other contexts
                    new_wheel_content = re.sub(r"cp3[0-9]+", "py3", new_wheel_content)
                    new_wheel_content = re.sub(r"cp3[0-9]+", "none", new_wheel_content)
                    new_zip.writestr(wheel_name, new_wheel_content)

        # Delete old wheel
        wheel_path.unlink()

        # Rename to py3-none platform format
        parts = Path(wheel_path.name).stem.split("-")
        if len(parts) >= 5 and parts[2].startswith("cp"):
            parts[2] = "py3"
            parts[3] = "none"
            new_name = "-".join(parts) + ".whl"
        else:
            new_name = wheel_path.name

        final_wheel = dist_dir / new_name
        new_wheel_path.rename(final_wheel)

        print(f"Wheel created: {final_wheel}")


if __name__ == "__main__":
    setup(
        cmdclass={"bdist_wheel": BdistWheelCommand},
    )
