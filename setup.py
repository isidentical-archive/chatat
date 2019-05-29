from pathlib import Path
from setuptools import setup, find_packages 

current_dir = Path(__file__).parent.resolve()

with open(current_dir / "README.md", encoding="utf-8") as f:
    long_description = f.read()
    
setup(
    name="chatat",
    version="0.1",
    packages=find_packages(),
    url="https://github.com/isidentical/chatat",
    description = "Twitch Chat Client",
    long_description = long_description,
    long_description_content_type = "text/markdown",
)
