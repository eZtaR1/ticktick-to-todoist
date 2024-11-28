"""
Core conversion logic for transforming TickTick CSV exports to Todoist import format.
With support for Todoist's 300 task per project limit and UTF-8 handling.
"""
import csv
import codecs
from pathlib import Path
from typing import List, Dict, Optional, TextIO
from math import ceil

class TickTickToTodoistConverter:
    TICKTICK_HEADER = [
        'Folder Name', 'List Name', 'Title', 'Kind', 'Tags', 'Content', 
        'Is Check list', 'Start Date', 'Due Date', 'Reminder', 'Repeat', 
        'Priority', 'Status', 'Created Time', 'Completed Time', 'Order', 
        'Timezone', 'Is All Day', 'Is Floating', 'Column Name', 
        'Column Order', 'View Mode', 'taskId', 'parentId'
    ]

    TODOIST_HEADER = [
        'TYPE', 'CONTENT', 'DESCRIPTION', 'PRIORITY', 'INDENT', 'AUTHOR',
        'RESPONSIBLE', 'DATE', 'DATE_LANG', 'TIMEZONE', 'DURATION', 'DURATION_UNIT'
    ]

    PRIORITY_MAP = {0: 4, 5: 3, 3: 2, 1: 1}  # TickTick to Todoist priority mapping
    TASKS_PER_PROJECT = 300  # Todoist's limit

    def __init__(self, include_priority: bool = True):
        self.include_priority = include_priority

    def clean_text(self, text: str) -> str:
        """Aggressively clean text for Todoist compatibility."""
        if not text:
            return ""
            
        # Basic string normalization
        text = text.strip()
        
        # Replace problematic characters
        replacements = {
            '"': '"',        # Smart quotes
            '"': '"',
            ''': "'",        # Smart apostrophes
            ''': "'",
            '–': '-',        # En dash
            '—': '-',        # Em dash
            '…': '...',      # Ellipsis
            '\u200b': '',    # Zero-width space
            '\u200c': '',    # Zero-width non-joiner
            '\u200d': '',    # Zero-width joiner
            '\ufeff': '',    # Byte order mark
            '\r': '\n',      # Carriage returns
            '\t': ' ',       # Tabs
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Remove emojis and other special characters
        cleaned = ''
        for char in text:
            # Keep only printable ASCII characters, newlines, and basic punctuation
            if (32 <= ord(char) <= 126) or char == '\n' or char in 'æøåÆØÅ':
                cleaned += char
                
        # Normalize whitespace
        cleaned = ' '.join(cleaned.split())
        
        return cleaned

    def clean_label_name(self, name: str) -> str:
        """Convert a string into a valid Todoist label."""
        if not name:
            return ""
            
        # Replace spaces and dashes with underscore
        cleaned = name.replace(' ', '_').replace('-', '_')
        
        # Keep only alphanumeric, underscore and Nordic characters
        cleaned = ''.join(c for c in cleaned if c.isalnum() or c == '_' or c in 'æøåÆØÅ')
        
        # Ensure no double underscores
        while '__' in cleaned:
            cleaned = cleaned.replace('__', '_')
            
        # Remove any leading or trailing underscores
        cleaned = cleaned.strip('_')
        
        return cleaned.lower()

    def read_ticktick_csv(self, file_path: Path) -> List[List[str]]:
        """Read and validate TickTick CSV file with proper UTF-8 handling."""
        try:
            # Use UTF-8-SIG to handle BOM if present
            with codecs.open(file_path, 'r', encoding='utf-8-sig') as f:
                # Skip metadata lines
                for _ in range(6):
                    next(f)
                
                reader = csv.reader(f)
                header = next(reader)
                
                if header != self.TICKTICK_HEADER:
                    raise ValueError("Invalid CSV file: Header doesn't match TickTick format")
                
                return list(reader)
        except UnicodeDecodeError:
            # Try with alternative encodings if UTF-8 fails
            try:
                with codecs.open(file_path, 'r', encoding='iso-8859-1') as f:
                    for _ in range(6):
                        next(f)
                    reader = csv.reader(f)
                    header = next(reader)
                    if header != self.TICKTICK_HEADER:
                        raise ValueError("Invalid CSV file: Header doesn't match TickTick format")
                    return list(reader)
            except Exception as e:
                raise ValueError(f"Could not read file with UTF-8 or ISO-8859-1 encoding: {str(e)}")

    def calculate_indents(self, tasks: List[List[str]]) -> Dict[str, int]:
        """Calculate indent levels for tasks based on parent-child relationships."""
        root_tasks = []
        child_tasks = {}
        indents = {}
        
        # Separate root tasks and build child task relationships
        for task in tasks:
            task_id = task[22]
            parent_id = task[23]
            
            if not parent_id:
                root_tasks.append(task_id)
            else:
                if parent_id not in child_tasks:
                    child_tasks[parent_id] = []
                child_tasks[parent_id].append(task_id)
        
        # Recursively set indent levels
        def set_indent_level(task_id: str, level: int):
            indents[task_id] = min(level, 4)  # Todoist only supports 4 levels of indentation
            if task_id in child_tasks:
                for child_id in child_tasks[task_id]:
                    set_indent_level(child_id, level + 1)
        
        # Process all root tasks
        for task_id in root_tasks:
            set_indent_level(task_id, 1)
        
        return indents

    def validate_csv_row(self, row: List[str]) -> bool:
        """Check if a CSV row contains any problematic characters."""
        try:
            # Try writing the row to a string buffer
            output = []
            writer = csv.writer(output)
            writer.writerow(row)
            # Convert back to check if it's valid
            reader = csv.reader(output)
            list(reader)
            return True
        except Exception:
            return False

    def create_todoist_task(self, task: List[str], indent: int) -> List[str]:
        """Convert a single TickTick task to Todoist format."""
        title = self.clean_text(task[2])
        content = self.clean_text(task[5])
        
        # Skip if title is empty after cleaning
        if not title:
            return []

        list_name = task[1]
        folder_name = task[0]
        status = task[12]
        due_date = task[8]
        
        # Collect labels
        labels = []
        
        # Add list and folder labels
        if list_name:
            labels.append(f"list_{self.clean_label_name(list_name)}")
        if folder_name:
            labels.append(f"folder_{self.clean_label_name(folder_name)}")
        
        # Add completed label if applicable
        if status == '2':
            labels.append('completed')
        
        # Add original tags
        if task[4]:  # Tags column
            labels.extend(self.clean_label_name(tag.strip()) for tag in task[4].split(','))
        
        # Build task content with labels
        task_content = title
        if labels:
            task_content += ' ' + ' '.join(f'@{label}' for label in labels)
        
        # Set priority
        priority = str(self.PRIORITY_MAP.get(int(task[11]), 4)) if self.include_priority else '4'
        
        return [
            'task',          # TYPE
            task_content,    # CONTENT
            content,        # DESCRIPTION
            priority,       # PRIORITY
            str(indent),    # INDENT
            '',            # AUTHOR
            '',            # RESPONSIBLE
            due_date,      # DATE
            'en',          # DATE_LANG
            'UTC',         # TIMEZONE
            '',            # DURATION
            'None'         # DURATION_UNIT
        ]
    def create_note_row(self, content: str) -> List[str]:
        """Create a note row for task description."""
        cleaned_content = self.clean_text(content)
        row = [
            'note',          # TYPE
            cleaned_content, # CONTENT
            '',             # DESCRIPTION
            '',             # PRIORITY
            '',             # INDENT
            '',             # AUTHOR
            '',             # RESPONSIBLE
            '',             # DATE
            'en',           # DATE_LANG
            'UTC',          # TIMEZONE
            '',             # DURATION
            'None'          # DURATION_UNIT
        ]

        # Validate the row, if invalid return empty note
        if not self.validate_csv_row(row):
            print(f"Warning: Had to remove note due to incompatible characters")
            return None
        return row

    def process_chunk(self, tasks: List[List[str]], chunk_number: int, total_chunks: int) -> List[List[str]]:
        """Process a chunk of tasks and add chunk information to labels."""
        processed_tasks = []
        for task in tasks:
            task = list(task)  # Create a copy of the task
            # Add chunk information to the content
            if total_chunks > 1:
                if task[4]:  # If there are existing tags
                    task[4] = f"{task[4]},part_{chunk_number}_of_{total_chunks}"
                else:
                    task[4] = f"part_{chunk_number}_of_{total_chunks}"
            processed_tasks.append(task)
        return processed_tasks

    def split_tasks_into_chunks(self, tasks: List[List[str]]) -> List[List[List[str]]]:
        """Split tasks into chunks of TASKS_PER_PROJECT."""
        if len(tasks) <= self.TASKS_PER_PROJECT:
            return [tasks]

        # Calculate number of chunks needed
        num_chunks = ceil(len(tasks) / self.TASKS_PER_PROJECT)
        chunks = []
        
        for i in range(num_chunks):
            start_idx = i * self.TASKS_PER_PROJECT
            end_idx = min((i + 1) * self.TASKS_PER_PROJECT, len(tasks))
            chunk = self.process_chunk(
                tasks[start_idx:end_idx], 
                chunk_number=i+1, 
                total_chunks=num_chunks
            )
            chunks.append(chunk)
        
        return chunks

    def convert(self, input_file: Path, output_dir: Optional[Path] = None) -> List[Path]:
        """Convert TickTick CSV to Todoist format, splitting into multiple files if needed."""
        # Set default output directory if none provided
        if output_dir is None:
            output_dir = input_file.parent
        else:
            output_dir.mkdir(parents=True, exist_ok=True)

        # Read and process tasks
        tasks = self.read_ticktick_csv(input_file)
        indents = self.calculate_indents(tasks)
        
        # Sort tasks based on hierarchy
        task_ids = list(indents.keys())
        tasks.sort(key=lambda x: task_ids.index(x[22]))
        
        # Split into chunks if necessary
        chunks = self.split_tasks_into_chunks(tasks)
        output_files = []
        
        # Process each chunk
        for i, chunk in enumerate(chunks):
            suffix = f"_part{i+1}" if len(chunks) > 1 else ""
            output_file = output_dir / f"todoist_import{suffix}.csv"
            
            # Convert chunk to Todoist format
            todoist_tasks = [self.TODOIST_HEADER]
            
            for task in chunk:
                # Add main task
                todoist_task = self.create_todoist_task(task, indents[task[22]])
                if todoist_task:
                    todoist_tasks.append(todoist_task)
                
                # Add note if task has description
                if task[5]:
                    note_row = self.create_note_row(task[5])
                    if note_row:  # Only add if valid
                        todoist_tasks.append(note_row)
            
            # Write output file
            with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(todoist_tasks)
            
            output_files.append(output_file)
            
            task_count = len([t for t in todoist_tasks if t[0] == 'task'])
            print(f"Created {output_file} with {task_count} tasks")
        
        return output_files