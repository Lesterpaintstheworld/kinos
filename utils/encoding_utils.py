import os
import fnmatch
import chardet
from utils.logger import Logger

class EncodingUtils:
    """Utility class for handling file encodings."""
    
    def __init__(self, model=None):
        self.logger = Logger(model=model)
        self.model = model

    def read_file_safely(self, filepath: str) -> str:
        """
        Read file content with robust encoding handling.
        
        Args:
            filepath (str): Path to file to read
            
        Returns:
            str: File content with normalized line endings
            
        Raises:
            Exception: If file cannot be read
        """
        try:
            # First verify if file is already valid UTF-8
            try:
                with open(filepath, 'rb') as f:
                    content = f.read()
                    if content.decode('utf-8'):
                        # File is already valid UTF-8, read normally
                        with open(filepath, 'r', encoding='utf-8', newline='') as f:
                            return f.read()
            except UnicodeDecodeError:
                pass  # Not UTF-8, continue to conversion

            # Try different encodings
            encodings = ['latin-1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    with open(filepath, 'rb') as f:
                        content = f.read()
                    decoded = content.decode(encoding)
                    
                    # Verify this isn't already UTF-8 encoded content
                    try:
                        if content.decode('utf-8'):
                            self.logger.debug(f"File {filepath} is already UTF-8")
                            return decoded
                    except UnicodeDecodeError:
                        # Not UTF-8, safe to convert
                        # Normalize line endings to system default without duplicating
                        lines = decoded.splitlines()
                        utf8_content = os.linesep.join(lines)
                        
                        # Only write back if content actually changed
                        if content != utf8_content.encode('utf-8'):
                            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                                f.write(utf8_content)
                            self.logger.info(f"✨ Converted {filepath} from {encoding} to UTF-8")
                        return utf8_content
                except UnicodeDecodeError:
                    continue
            
            # If all encodings fail, try binary read with replacement
            self.logger.warning(f"⚠️ All encodings failed for {filepath}, using replacement mode")
            with open(filepath, 'rb') as f:
                content = f.read()
                decoded = content.decode('utf-8', errors='replace')
                # Normalize line endings
                lines = decoded.splitlines()
                normalized = os.linesep.join(lines)
                
                # Only write back if absolutely necessary
                try:
                    original = content.decode('utf-8')
                    if original == normalized:
                        return original
                except UnicodeDecodeError:
                    with open(filepath, 'w', encoding='utf-8', newline='') as f:
                        f.write(normalized)
                    self.logger.warning(f"⚠️ Forced UTF-8 decode for {filepath}")
                return normalized
                
        except Exception as e:
            self.logger.error(f"Failed to read {filepath}: {str(e)}")
            raise

    def convert_to_utf8(self, filepath: str) -> bool:
        """
        Convert a file to UTF-8 encoding.
        
        Args:
            filepath (str): Path to file to convert
            
        Returns:
            bool: True if conversion was successful
            
        Raises:
            Exception: If file cannot be converted
        """
        try:
            # First try to detect current encoding
            with open(filepath, 'rb') as f:
                raw = f.read()
            detected = chardet.detect(raw)
            
            if detected['encoding']:
                self.logger.info(f"🔍 Detected {filepath} encoding as: {detected['encoding']} (confidence: {detected['confidence']})")
                
                # Si c'est déjà en UTF-8, ne rien faire
                if detected['encoding'].lower().replace('-', '') == 'utf8':
                    self.logger.debug(f"✓ {filepath} is already UTF-8")
                    return True
            
                # Read with detected encoding
                content = raw.decode(detected['encoding'])
            
                # Normaliser les retours à la ligne
                content = '\n'.join(line.rstrip() for line in content.splitlines())
            
                # Write back in UTF-8
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                self.logger.success(f"✨ Converted {filepath} to UTF-8")
                return True
                
            else:
                # If detection failed, try common encodings
                encodings = ['latin-1', 'cp1252', 'iso-8859-1']
                for encoding in encodings:
                    try:
                        content = raw.decode(encoding)
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        self.logger.success(f"✨ Converted {filepath} from {encoding} to UTF-8")
                        return True
                    except UnicodeDecodeError:
                        continue
                        
                raise ValueError(f"Could not detect or convert encoding for {filepath}")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to convert {filepath} to UTF-8: {str(e)}")
            raise

    def convert_all_to_utf8(self, ignore_patterns: list = None):
        """Convert all text files in the project to UTF-8."""
        try:
            # Use default ignore patterns if none provided
            if ignore_patterns is None:
                ignore_patterns = ['.git*', '.aider*', '__pycache__', '*.pyc']
            
            # Track conversion results
            results = {
                'converted': [],
                'failed': [],
                'skipped': []
            }
            
            # Process all files
            for root, _, files in os.walk('.'):
                for file in files:
                    if file.endswith(('.md', '.txt', '.py')):  # Add other extensions as needed
                        filepath = os.path.join(root, file)
                        
                        # Skip ignored files
                        if any(fnmatch.fnmatch(filepath, pattern) for pattern in ignore_patterns):
                            results['skipped'].append(filepath)
                            continue
                            
                        try:
                            # Check if already UTF-8
                            try:
                                with open(filepath, 'r', encoding='utf-8') as f:
                                    f.read()
                                self.logger.debug(f"✅ {filepath} is already UTF-8")
                                continue
                            except UnicodeDecodeError:
                                # Not UTF-8, convert it
                                if self.convert_to_utf8(filepath):
                                    results['converted'].append(filepath)
                        except Exception as e:
                            self.logger.error(f"❌ Failed to process {filepath}: {str(e)}")
                            results['failed'].append((filepath, str(e)))
            
            # Log summary
            self.logger.success(
                f"\n📊 Conversion Summary:\n"
                f"   - Converted: {len(results['converted'])} files\n"
                f"   - Failed: {len(results['failed'])} files\n"
                f"   - Skipped: {len(results['skipped'])} files"
            )
            
            if results['failed']:
                self.logger.warning("\n⚠️ Failed conversions:")
                for filepath, error in results['failed']:
                    self.logger.warning(f"   - {filepath}: {error}")
                    
            return results
            
        except Exception as e:
            self.logger.error(f"❌ UTF-8 conversion failed: {str(e)}")
            raise
