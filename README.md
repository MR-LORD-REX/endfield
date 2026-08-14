# Endfield

A Python library for fetching and parsing player data from the Enka Network API for **Endfield**.

[![PyPI version](https://img.shields.io/pypi/v/endfield-py.svg)](https://pypi.org/project/endfield-py/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE.txt)

## Overview

**Endfield** is an async Python library that provides easy access to player game data from the Enka Network API. It allows developers to retrieve comprehensive information about players, their characters, weapons, equipment, and computed statistics.

## Features

-  **Async Support**: Built with asyncio for efficient concurrent requests
-  **Complete Data Models**: Pydantic-based models for type-safe data handling
-  **Player Showcase Data**: Fetch player profiles and their character showcases
-  **Character Information**: Get detailed character data including skills, talents, and stats
-  **Equipment & Weapons**: Access equipment and weapon information
-  **Stat Computation**: Calculate final character statistics with modifiers
-  **Asset Resolution**: Built-in asset resolution with local JSON data
-  **Update Checking**: Check for and download library updates
-  **Session Management**: Flexible session handling with context managers

## Installation

### From PyPI

```bash
pip install endfield-py
```

### From GitHub

```bash
pip install git+https://github.com/MR-LORD-REX/endfield.git
```

### Manual Installation

```bash
git clone https://github.com/MR-LORD-REX/endfield.git
cd endfield
pip install -e .
```

## Requirements

- Python 3.8+
- aiohttp >= 3.8.0
- pydantic >= 2.0.0

## Quick Start

### Basic Usage

```python
import asyncio
from endfield import Endfield

async def main():
    async with Endfield() as client:
        await client.update_assets()
        showcase = await client.get_showcase(uid=4225399080)
        print(showcase)

asyncio.run(main())
```


### Enable Debug Logging

```python
async with Endfield(debug=True) as client:
    showcase = await client.get_showcase(uid=4225399080)
```

## Documentation

Comprehensive documentation for all classes, methods, and data models is hosted on GitHub Pages:

👉 **[Endfield SDK Documentation](https://MR-LORD-REX.github.io/endfield/)**

#### How to get the token?

- Open the [skport](https://www.skport.com/) website (official endfield website) and log in with game account
- Then go to [THIS API](https://web-api.skport.com/cookie_store/account_token) endpoint (official internal API) to get the token

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues on the [GitHub repository](https://github.com/MR-LORD-REX/endfield).

### Development Setup

```bash
git clone https://github.com/MR-LORD-REX/endfield.git
cd endfield
pip install -e .
```

## License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details.

## Disclaimer

This is an unofficial library. Endfield is a trademark of their respective owners. This library is not affiliated with or endorsed by the game developers. Use this library responsibly and in accordance with the Enka Network API terms of service.

## Support

For issues, questions, or suggestions, please open an issue on the [GitHub repository](https://github.com/MR-LORD-REX/endfield/issues).

## Credits

- Built by [MR-LORD-REX](https://github.com/MR-LORD-REX) , [telegram](https://t.me/The_Prime_Mover)
- Data source: [Enka Network](https://enka.network)
- Blueprints data source: [endfieldtools.dev](https://endfieldtools.dev/)

## Changelog

### Version 1.1.4

- game V1.4 asset update
- Fixed issue where stats were not being computed correctly
- folder structure changed 
- older versions " before v1.1.1 " will not support auto update anymore, you will have to manually update the library to get the latest assets or just update the library to the latest version
- added proxies 


---

## NOTE 

- Computation of final character stats are done by the currently known formulas, some of them might be inaccurate , feel free to contribute if you encounter any discrepancies or have suggestions for improvement.

**Happy Endfielding**
