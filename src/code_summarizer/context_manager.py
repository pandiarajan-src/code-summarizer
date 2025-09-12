"""
Context management for handling token limits and batching files
"""
import tiktoken
from typing import List, Dict, Any
import yaml

class ContextManager:
    def __init__(self, config_path: str = 'config.yaml'):
        self.config = self._load_config(config_path)
        
        # Get model configuration
        llm_config = self.config.get('llm', {})
        self.model_name = llm_config.get('model', 'gpt-4o')
        self.max_context_tokens = llm_config.get('max_context_tokens', 128000)
        
        # Reserve tokens for prompt template and response
        self.prompt_overhead = 2000
        self.response_tokens = llm_config.get('max_tokens', 4000)
        self.available_tokens = self.max_context_tokens - self.prompt_overhead - self.response_tokens
        
        # Initialize tokenizer
        try:
            self.tokenizer = tiktoken.encoding_for_model(self.model_name)
        except KeyError:
            # Fallback to cl100k_base for unknown models
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return {}
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using the model's tokenizer"""
        try:
            return len(self.tokenizer.encode(text))
        except Exception:
            # Fallback: rough estimation (4 chars per token average)
            return len(text) // 4
    
    def estimate_file_tokens(self, file_data: Dict[str, Any]) -> int:
        """Estimate tokens needed for a single file including metadata"""
        content_tokens = self.count_tokens(file_data['content'])
        
        # Add estimated tokens for metadata (filename, path, etc.)
        metadata_tokens = self.count_tokens(
            f"File: {file_data['name']}\nPath: {file_data['path']}\nLines: {file_data['lines']}\n"
        )
        
        return content_tokens + metadata_tokens
    
    def create_batches(self, files_data: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Create batches of files that fit within context limits
        
        Returns:
            List of file batches, each batch fits within token limits
        """
        if not files_data:
            return []
        
        # Calculate token count for each file
        file_tokens = []
        for file_data in files_data:
            tokens = self.estimate_file_tokens(file_data)
            file_tokens.append((file_data, tokens))
        
        # Sort files by token count (largest first for better packing)
        file_tokens.sort(key=lambda x: x[1], reverse=True)
        
        batches = []
        current_batch = []
        current_tokens = 0
        
        for file_data, token_count in file_tokens:
            # Check if single file exceeds limit
            if token_count > self.available_tokens:
                # Handle oversized files by truncating content
                truncated_file = self._truncate_file_content(file_data, self.available_tokens)
                batches.append([truncated_file])
                continue
            
            # Check if adding this file would exceed the limit
            if current_tokens + token_count > self.available_tokens and current_batch:
                # Start new batch
                batches.append(current_batch)
                current_batch = [file_data]
                current_tokens = token_count
            else:
                # Add to current batch
                current_batch.append(file_data)
                current_tokens += token_count
        
        # Add final batch if not empty
        if current_batch:
            batches.append(current_batch)
        
        return batches
    
    def _truncate_file_content(self, file_data: Dict[str, Any], max_tokens: int) -> Dict[str, Any]:
        """
        Truncate file content to fit within token limit while preserving structure
        """
        # Reserve tokens for metadata and truncation message
        metadata_tokens = 200
        truncation_message = "\n\n[... Content truncated due to size limits ...]\n"
        truncation_tokens = self.count_tokens(truncation_message)
        
        available_for_content = max_tokens - metadata_tokens - truncation_tokens
        
        # Binary search to find optimal truncation point
        content = file_data['content']
        lines = content.splitlines()
        
        # Try to keep as many complete lines as possible
        truncated_lines = []
        current_tokens = 0
        
        for line in lines:
            line_tokens = self.count_tokens(line + '\n')
            if current_tokens + line_tokens > available_for_content:
                break
            truncated_lines.append(line)
            current_tokens += line_tokens
        
        # Create truncated file data
        truncated_content = '\n'.join(truncated_lines) + truncation_message
        
        truncated_file = file_data.copy()
        truncated_file['content'] = truncated_content
        truncated_file['truncated'] = True
        truncated_file['original_lines'] = file_data['lines']
        truncated_file['truncated_lines'] = len(truncated_lines)
        
        return truncated_file
    
    def get_batch_info(self, batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get information about a batch"""
        total_tokens = sum(self.estimate_file_tokens(file_data) for file_data in batch)
        total_files = len(batch)
        total_lines = sum(file_data['lines'] for file_data in batch)
        
        languages = set()
        for file_data in batch:
            ext = file_data['extension'].lower()
            lang = self._extension_to_language(ext)
            if lang:
                languages.add(lang)
        
        return {
            'total_files': total_files,
            'total_tokens': total_tokens,
            'total_lines': total_lines,
            'languages': list(languages),
            'files': [{'name': f['name'], 'lines': f['lines'], 'size': f['size']} for f in batch]
        }
    
    def _extension_to_language(self, extension: str) -> str:
        """Map file extension to programming language"""
        ext_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.jsx': 'JavaScript',
            '.tsx': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.h': 'C',
            '.hpp': 'C++',
            '.cs': 'C#',
            '.swift': 'Swift',
            '.go': 'Go',
            '.rs': 'Rust',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.scala': 'Scala',
            '.kt': 'Kotlin',
            '.dart': 'Dart',
            '.r': 'R',
            '.m': 'Objective-C',
            '.sh': 'Shell',
            '.sql': 'SQL'
        }
        
        return ext_map.get(extension.lower(), 'Unknown')
    
    def optimize_batching_strategy(self, files_data: List[Dict[str, Any]]) -> str:
        """
        Analyze files and suggest optimal batching strategy
        """
        total_files = len(files_data)
        total_tokens = sum(self.estimate_file_tokens(f) for f in files_data)
        
        if total_tokens <= self.available_tokens:
            return "single_batch"
        elif total_files <= 10:
            return "file_by_file"  
        else:
            return "smart_batching"