#!/usr/bin/env python
from __future__ import annotations
import itertools

import logging
from contextlib import contextmanager
import os
from multiprocessing.dummy import Pool
import configparser
import shutil
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

DIST_DIR = Path("dist")
DIST_DIR.mkdir(exist_ok=True)

SERVIVE_PKG_SETUP_PY = """\
#!/usr/bin/env python
from setuptools import setup

setup(
    name='botocore-a-la-carte-{service}',
    version="{version}",
    description='{service} data for botocore. See the `botocore-a-la-carte` package for more info.',
    author='Amazon Web Services',
    url='https://github.com/thejcannon/botocore-a-la-carte',
    scripts=[],
    packages=["botocore"],
    package_data={{
        'botocore': ['data/{service}/*/*.json'],
    }},
    include_package_data=True,
    license="Apache License 2.0",
    python_requires=">= 3.7",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ]
)
"""

@contextmanager
def _temp_servicedir(service: str):
    service_pkg_path = Path(f"botocore-a-la-carte-{service}")
    try:
        yield service_pkg_path
    finally:
        shutil.rmtree(service_pkg_path)

def _build_dist(arg):
    version, service = arg
    with _temp_servicedir(service) as service_pkg_path:
        logger.info("Service: %s", service)

        service_pkg_data_path = service_pkg_path / "botocore" / "data"
        service_pkg_data_path.mkdir(parents=True)
        shutil.copyfile("LICENSE.txt", service_pkg_path / "LICENSE.txt")
        os.rename(f"botocore/data/{service}", service_pkg_data_path/ service)
        (service_pkg_path / "setup.py").write_text(
            SERVIVE_PKG_SETUP_PY.format(service=service, version=version)
        )
        subprocess.run(
            [sys.executable, "setup.py", "sdist", "bdist_wheel"],
            cwd=service_pkg_path,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for dist in (service_pkg_path / "dist").iterdir():
            os.rename(dist, DIST_DIR / dist.name)


def main(version: str, readme_path: str) -> None:
    logging.basicConfig(level=logging.INFO)

    services = sorted(p.name for p in Path("botocore/data").iterdir() if p.is_dir())
    with Pool(os.cpu_count()) as pool:
        for _ in pool.map(_build_dist, zip(itertools.repeat(version), services)):
            pass


    # Now for the base package
    setup_py_path = Path("setup.py")
    setup_py_path.write_text(
        setup_py_path.read_text().replace(
            "name='botocore'", "name='botocore-a-la-carte'"
        ).replace(
            "url='https://github.com/boto/botocore'",
            "url='https://github.com/thejcannon/botocore-a-la-carte'",
        ).replace(
            "description='Low-level, data-driven core of boto 3.'",
            "description='botocore re-uploaded with a-la-carte data packages.'"
        )
    )
    Path("README.rst").write_text(Path(readme_path).read_text())

    setup_config = configparser.ConfigParser()
    setup_config.read('setup.cfg')
    for service in services:
        setup_config["options.extras_require"][service] = f"botocore-a-la-carte-{service}=={version}"
    with open("setup.cfg", mode="w") as f:
        setup_config.write(f)

    subprocess.run(
        [sys.executable, "setup.py", "sdist", "bdist_wheel"],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    subprocess.run(["twine", "upload", "--disable-progress-bar", "--skip-existing", "dist/*"], check=True)


if __name__ == "__main__":
    version = sys.argv[1]
    readme_path = sys.argv[2]
    main(version, readme_path)

