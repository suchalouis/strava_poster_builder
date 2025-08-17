"""
Gestionnaire de palette de couleurs pour les posters Strava
Permet de personnaliser les couleurs des graphiques, cartes et éléments visuels
"""

from typing import Dict, Optional
import re
import logging

logger = logging.getLogger(__name__)


class ColorPalette:
    """
    Gestionnaire de palette de couleurs personnalisable pour les posters
    
    Permet de définir jusqu'à 5 couleurs personnalisées qui remplacent
    les couleurs par défaut dans tous les composants visuels.
    """
    
    def __init__(self, color_dict: Optional[Dict[str, str]] = None):
        """
        Initialise la palette de couleurs
        
        Args:
            color_dict: Dictionnaire avec les couleurs personnalisées
                       {first_color, second_color, third_color, fourth_color, fifth_color}
                       Toutes les couleurs sont optionnelles
        """
        # Couleurs par défaut (actuelles du système)
        self._default_colors = {
            'first_color': '#FC4C02',    # Orange Strava principal (tracés, barres)
            'second_color': '#22C55E',   # Vert (point de départ)
            'third_color': '#EF4444',    # Rouge (point d'arrivée)
            'fourth_color': '#333333',   # Gris foncé (axes, labels)
            'fifth_color': '#999999'     # Gris clair (erreurs, textes secondaires)
        }
        
        # Stocker les couleurs personnalisées
        self._custom_colors = {}
        if color_dict:
            self._set_colors(color_dict)
    
    def _set_colors(self, color_dict: Dict[str, str]) -> None:
        """
        Définit les couleurs personnalisées avec validation
        
        Args:
            color_dict: Dictionnaire des couleurs à définir
            
        Raises:
            ValueError: Si une couleur n'est pas au format hexadécimal valide
        """
        valid_keys = {'first_color', 'second_color', 'third_color', 'fourth_color', 'fifth_color'}
        
        for key, color in color_dict.items():
            if key not in valid_keys:
                logger.warning(f"Clé de couleur invalide ignorée: {key}")
                continue
                
            if not self._is_valid_hex_color(color):
                raise ValueError(f"Couleur invalide pour {key}: {color}. Format attendu: #RRGGBB ou #RGB")
            
            # Normaliser au format long si nécessaire
            normalized_color = self._normalize_hex_color(color)
            self._custom_colors[key] = normalized_color
            logger.debug(f"Couleur définie: {key} = {normalized_color}")
    
    def _is_valid_hex_color(self, color: str) -> bool:
        """
        Valide qu'une couleur est au format hexadécimal
        
        Args:
            color: Couleur à valider (ex: "#FF0000" ou "#F00")
            
        Returns:
            True si la couleur est valide, False sinon
        """
        if not isinstance(color, str):
            return False
        
        # Pattern pour #RGB ou #RRGGBB
        pattern = r'^#([A-Fa-f0-9]{3}|[A-Fa-f0-9]{6})$'
        return bool(re.match(pattern, color))
    
    def _normalize_hex_color(self, color: str) -> str:
        """
        Normalise une couleur hex au format long (#RRGGBB)
        
        Args:
            color: Couleur au format #RGB ou #RRGGBB
            
        Returns:
            Couleur normalisée au format #RRGGBB
        """
        if len(color) == 4:  # Format #RGB
            r, g, b = color[1], color[2], color[3]
            return f"#{r}{r}{g}{g}{b}{b}".upper()
        else:  # Format #RRGGBB
            return color.upper()
    
    def get_primary_color(self) -> str:
        """Couleur principale (tracés, barres d'histogramme)"""
        return self._custom_colors.get('first_color', self._default_colors['first_color'])
    
    def get_start_point_color(self) -> str:
        """Couleur du point de départ"""
        return self._custom_colors.get('second_color', self._default_colors['second_color'])
    
    def get_end_point_color(self) -> str:
        """Couleur du point d'arrivée"""
        return self._custom_colors.get('third_color', self._default_colors['third_color'])
    
    def get_axis_color(self) -> str:
        """Couleur des axes et labels"""
        return self._custom_colors.get('fourth_color', self._default_colors['fourth_color'])
    
    def get_secondary_text_color(self) -> str:
        """Couleur des textes secondaires et messages d'erreur"""
        return self._custom_colors.get('fifth_color', self._default_colors['fifth_color'])
    
    def get_stroke_color(self) -> str:
        """Couleur des bordures (version plus foncée de la couleur principale)"""
        primary = self.get_primary_color()
        # Assombrir la couleur principale pour les bordures
        return self._darken_color(primary, 0.2)
    
    def _darken_color(self, hex_color: str, factor: float) -> str:
        """
        Assombrit une couleur hexadécimale
        
        Args:
            hex_color: Couleur au format #RRGGBB
            factor: Facteur d'assombrissement (0.0 = pas de changement, 1.0 = noir)
            
        Returns:
            Couleur assombrie au format #RRGGBB
        """
        try:
            # Extraire les composantes RGB
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16) 
            b = int(hex_color[4:6], 16)
            
            # Assombrir chaque composante
            r = max(0, int(r * (1 - factor)))
            g = max(0, int(g * (1 - factor)))
            b = max(0, int(b * (1 - factor)))
            
            return f"#{r:02X}{g:02X}{b:02X}"
            
        except Exception as e:
            logger.warning(f"Erreur lors de l'assombrissement de {hex_color}: {e}")
            return hex_color  # Retourner la couleur originale en cas d'erreur
    
    def get_color(self, key: str) -> Optional[str]:
        """
        Récupère une couleur par sa clé
        
        Args:
            key: Clé de couleur (first_color, second_color, etc.)
            
        Returns:
            Couleur hexadécimale ou None si la clé n'existe pas
        """
        if key in self._custom_colors:
            return self._custom_colors[key]
        elif key in self._default_colors:
            return self._default_colors[key]
        else:
            return None
    
    def get_all_colors(self) -> Dict[str, str]:
        """
        Récupère toutes les couleurs (personnalisées + défaut)
        
        Returns:
            Dictionnaire complet des couleurs
        """
        colors = self._default_colors.copy()
        colors.update(self._custom_colors)
        return colors
    
    def update_colors(self, color_dict: Dict[str, str]) -> None:
        """
        Met à jour les couleurs personnalisées
        
        Args:
            color_dict: Nouvelles couleurs à définir
        """
        self._set_colors(color_dict)
    
    def reset_to_defaults(self) -> None:
        """Remet toutes les couleurs aux valeurs par défaut"""
        self._custom_colors.clear()
        logger.info("Palette de couleurs remise aux valeurs par défaut")
    
    def has_custom_colors(self) -> bool:
        """
        Vérifie si des couleurs personnalisées sont définies
        
        Returns:
            True si au moins une couleur personnalisée est définie
        """
        return len(self._custom_colors) > 0
    
    def get_template_placeholders(self) -> Dict[str, str]:
        """
        Génère les placeholders pour les templates SVG
        
        Returns:
            Dictionnaire des placeholders de couleurs pour les templates
        """
        return {
            'COLOR_PRIMARY': self.get_primary_color(),
            'COLOR_START': self.get_start_point_color(),
            'COLOR_END': self.get_end_point_color(),
            'COLOR_AXIS': self.get_axis_color(),
            'COLOR_SECONDARY': self.get_secondary_text_color(),
            'COLOR_STROKE': self.get_stroke_color()
        }
    
    def __str__(self) -> str:
        """Représentation textuelle de la palette"""
        colors = self.get_all_colors()
        custom_info = f" ({len(self._custom_colors)} personnalisées)" if self.has_custom_colors() else " (par défaut)"
        return f"ColorPalette{custom_info}: {colors}"


def create_default_palette() -> ColorPalette:
    """
    Crée une palette avec les couleurs par défaut
    
    Returns:
        Palette de couleurs par défaut
    """
    return ColorPalette()


def create_custom_palette(first_color: Optional[str] = None,
                         second_color: Optional[str] = None,
                         third_color: Optional[str] = None,
                         fourth_color: Optional[str] = None,
                         fifth_color: Optional[str] = None) -> ColorPalette:
    """
    Crée une palette avec des couleurs personnalisées
    
    Args:
        first_color: Couleur principale (tracés, barres)
        second_color: Couleur point de départ
        third_color: Couleur point d'arrivée
        fourth_color: Couleur axes et labels
        fifth_color: Couleur textes secondaires
        
    Returns:
        Palette de couleurs personnalisée
    """
    color_dict = {}
    
    if first_color:
        color_dict['first_color'] = first_color
    if second_color:
        color_dict['second_color'] = second_color
    if third_color:
        color_dict['third_color'] = third_color
    if fourth_color:
        color_dict['fourth_color'] = fourth_color
    if fifth_color:
        color_dict['fifth_color'] = fifth_color
    
    return ColorPalette(color_dict)