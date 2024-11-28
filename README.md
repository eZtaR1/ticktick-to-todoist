# TickTick to Todoist Converter

A Python utility to convert TickTick CSV exports to Todoist CSV import format, with support for:
- Task titles and descriptions
- Due dates
- Completed tasks
- Labels (converted from TickTick folders, lists, and tags)
- Task hierarchies (parent/child relationships)
- Task priorities
- Completion status
- UTF-8 encoding handling
- Todoist's 300 task per project limit

## Features

- Preserves task hierarchies with proper indentation
- Converts TickTick folders and lists to Todoist labels
- Handles special characters and encoding issues
- Automatically splits large exports into multiple files
- Cleans and normalizes text for Todoist compatibility

## Installation

```bash
# Clone the repository
git clone https://github.com/eZtaR1/ticktick-to-todoist.git
cd ticktick-to-todoist

# Create and activate virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

1. Export your tasks from TickTick:
   - Go to TickTick Settings
   - Select "Generate backup", under "Backup and Restore" under "Account"
   - Save it somewhere useful

2. Run the converter:
```bash
python -m ticktick_to_todoist.cli path/to/your/ticktick_export.csv
```

3. Import the generated file(s) into Todoist:
   - Go to Todoist Settings
   - Select "Import"
   - Choose "Import from template (CSV)"
   - Select the generated `todoist_import.csv` file(s)


## Requirements

- Python 3.7 or higher
- Required packages are listed in `requirements.txt`

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Thanks to mrzmyr inspiration via his converter https://github.com/mrzmyr/ticktick-to-todoist

## Support

If you encounter any issues or have questions, please create an issue in the GitHub repository.
