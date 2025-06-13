"""Validadores para os modelos de dados"""

import re
from typing import Any, Optional

class ValidationError(Exception):
    """Exceção para erros de validação"""
    pass

class Validators:
    """Classe com métodos de validação"""
    
    # Regex patterns
    TWITCH_USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]{4,25}$")
    DISCORD_ID_PATTERN = re.compile(r"^\d{17,19}$")
    HEX_COLOR_PATTERN = re.compile(r"^#?[0-9A-Fa-f]{6}$")
    
    @staticmethod
    def validate_twitch_username(username: str) -> bool:
        """Valida username da Twitch"""
        if not username:
            return False
        return bool(Validators.TWITCH_USERNAME_PATTERN.match(username))
    
    @staticmethod
    def validate_discord_id(discord_id: Any) -> bool:
        """Valida ID do Discord"""
        if isinstance(discord_id, int):
            discord_id = str(discord_id)
        if not isinstance(discord_id, str):
            return False
        return bool(Validators.DISCORD_ID_PATTERN.match(discord_id))
    
    @staticmethod
    def validate_hex_color(color: Any) -> bool:
        """Valida cor hexadecimal"""
        if isinstance(color, int):
            return 0x000000 <= color <= 0xFFFFFF
        if isinstance(color, str):
            return bool(Validators.HEX_COLOR_PATTERN.match(color))
        return False
    
    @staticmethod
    def validate_template_variables(template: str) -> bool:
        """Valida se o template contém variáveis válidas"""
        valid_variables = [
            "{title}", "{streamer}", "{creator}", 
            "{views}", "{duration}", "{url}",
            "{username}", "{timestamp}"
        ]
        
        # Encontrar todas as variáveis no template
        variables = re.findall(r'\{[^}]+\}', template)
        
        # Verificar se todas as variáveis são válidas
        for var in variables:
            if var not in valid_variables:
                return False
        
        return True
    
    @staticmethod
    def validate_filter_range(min_val: float, max_val: float) -> bool:
        """Valida range de filtros"""
        return min_val >= 0 and max_val >= min_val
    
    @staticmethod
    def sanitize_keywords(keywords: list) -> list:
        """Sanitiza lista de palavras-chave"""
        if not keywords:
            return []
        
        sanitized = []
        for keyword in keywords:
            if isinstance(keyword, str) and keyword.strip():
                sanitized.append(keyword.strip().lower())
        
        return list(set(sanitized))  # Remove duplicatas
    
    @staticmethod
    def validate_broadcaster_id(broadcaster_id: str) -> bool:
        """Valida ID do broadcaster da Twitch"""
        if not broadcaster_id:
            return False
        return broadcaster_id.isdigit() and len(broadcaster_id) > 0