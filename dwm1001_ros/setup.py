import os
from glob import glob
from setuptools import find_packages, setup

package_name = "dwm1001_ros"

setup(
    name=package_name,
    version="2.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Bohumil Brož",
    maintainer_email="brozbohu@fel.cvut.cz",
    description="ROS 2 driver for the Qorvo DWM-1001 UWB module",
    license="TODO",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "uwb_tag = dwm1001_ros.uwb_tag:main",
            "uwb_pose_publisher = dwm1001_ros.uwb_pose_publisher:main",
        ],
    },
)
