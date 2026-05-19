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
        # Fetch player showcase data
        showcase = await client.get_showcase(uid=4225399080)
        print(showcase)

asyncio.run(main())
```


### Enable Debug Logging

```python
async with Endfield(debug=True) as client:
    showcase = await client.get_showcase(uid=4225399080)
```

## API Reference

### Endfield Client

#### Constructor

```python
Endfield(
    session: Optional[aiohttp.ClientSession] = None,
    debug: bool = False
)
```

**Parameters:**

- `session`: Optional external aiohttp session
- `debug`: Enable debug logging (default: False)

#### Methods

##### `get_showcase(uid: int | str)`

Fetch complete player showcase data including all characters, equipment, and weapons.

```python
showcase = await client.get_showcase(uid=4225399080)
```

**Returns:** `ShowcaseData` - Complete player showcase information with all characters

##### `get_character_showcase(uid: int | str, index: int = 0)`

Fetch detailed data for a specific character in the player's showcase.

```python
char_data = await client.get_character_showcase(uid=4225399080, index=0)
```

**Parameters:**

- `uid`: Player UID
- `index`: Character index (0-based, default: 0)

**Returns:** `CharacterData` - Detailed character data including skills, talents, and computed statistics

##### `get_profile(uid: int | str)`

Fetch player profile information only.

```python
profile = await client.get_profile(uid=4225399080)
```

**Returns:** `PlayerProfile` - Player account and character list information

##### `check_for_updates()`

Check for library updates.

```python
await client.check_for_updates()
```

##### `close()`

Close the client session.

```python
await client.close()
```

## Data Models

The library provides comprehensive Pydantic models for type-safe data handling:

- **ShowcaseData**: Complete player showcase information
- **PlayerProfile**: Player account information
- **ProfileCharacter**: Character showcase data
- **CharacterData**: Detailed character information including skills and talents
- **WeaponData**: Weapon information and skills
- **EquipData**: Equipment data with stat modifiers
- **ComputedStats**: Final calculated character statistics

## Examples

### Fetch Player Profile

```python
async with Endfield() as client:
    showcase = await client.get_showcase(uid="your_uid_here")
    profile = showcase.player_info
    print(f"Player: {profile.player_name}")
    print(f"Level: {profile.level}")
```

### Get Character Information

```python
async with Endfield() as client:
    showcase = await client.get_showcase(uid="your_uid_here")
    for char in showcase.characters:
        print(f"Character: {char.name}")
        print(f"Level: {char.level}")
        print(f"Stats: {char.stats}")
```

### Check Weapon Information

```python
async with Endfield() as client:
    showcase = await client.get_showcase(uid="your_uid_here")
    for char in showcase.characters:
        if char.weapon:
            print(f"{char.name}'s Weapon: {char.weapon.name}")
            print(f"Level: {char.weapon.level}")
```

## Error Handling

The library provides specific exceptions for error handling:

```python
from endfield.errors import APIError, CharacterNotFoundError, WeaponNotFoundError

try:
    async with Endfield() as client:
        showcase = await client.get_showcase(uid="invalid_uid")
except APIError as e:
    print(f"API Error: {e}")
except CharacterNotFoundError as e:
    print(f"Character not found: {e}")
except WeaponNotFoundError as e:
    print(f"Weapon not found: {e}")
```


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

## Changelog

### Version 1.0.5

- Added medals data to player profile
- Updated data models to include medals
- Improved error handling for character processing

---

## NOTE 

- Computation of final character stats are done by the currently known formulas, some of them might be inaccurate , feel free to contribute if you encounter any discrepancies or have suggestions for improvement.

**Happy Endfielding**
