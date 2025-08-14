"""
Module de gestion des templates SVG pour les posters Strava
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class TemplateManager:
    """Gestionnaire des templates SVG pour la génération de posters"""
    
    def __init__(self, template_path: Optional[str] = None):
        """
        Initialise le gestionnaire de template
        
        Args:
            template_path: Chemin vers le template SVG (optionnel)
        """
        if template_path:
            self.template_path = Path(template_path)
        else:
            # Template par défaut relatif au projet
            self.template_path = Path(__file__).parent.parent.parent / "poster_framework.svg"
        
        self.template_content: Optional[str] = None
        self._load_template()
    
    def _load_template(self) -> None:
        """Charge le template SVG depuis le fichier"""
        try:
            if not self.template_path.exists():
                raise FileNotFoundError(f"Template SVG non trouvé: {self.template_path}")
            
            with open(self.template_path, 'r', encoding='utf-8') as f:
                self.template_content = f.read()
                
            logger.info(f"Template SVG chargé: {self.template_path}")
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement du template: {e}")
            raise
    
    def get_template_content(self) -> str:
        """
        Récupère le contenu du template
        
        Returns:
            Contenu du template SVG
            
        Raises:
            RuntimeError: Si le template n'est pas chargé
        """
        if not self.template_content:
            raise RuntimeError("Template SVG non chargé")
        
        return self.template_content
    
    def reload_template(self) -> None:
        """Recharge le template depuis le fichier"""
        self._load_template()
    
    def replace_placeholders(self, content: str, replacements: Dict[str, str]) -> str:
        """
        Remplace les placeholders dans le contenu SVG
        
        Args:
            content: Contenu SVG avec placeholders
            replacements: Dict des remplacements {placeholder: valeur}
            
        Returns:
            Contenu SVG avec placeholders remplacés
        """
        result = content
        for placeholder, value in replacements.items():
            # S'assurer que le placeholder est au bon format {{PLACEHOLDER}}
            if not placeholder.startswith('{{') or not placeholder.endswith('}}'):
                placeholder = f'{{{{{placeholder}}}}}'
            
            result = result.replace(placeholder, str(value))
        
        return result
    
    def create_poster_content(self, replacements: Dict[str, str]) -> str:
        """
        Crée le contenu SVG final du poster
        
        Args:
            replacements: Dict des remplacements pour les placeholders
            
        Returns:
            Contenu SVG final du poster
        """
        template_content = self.get_template_content()
        return self.replace_placeholders(template_content, replacements)