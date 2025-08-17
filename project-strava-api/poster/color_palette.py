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
                       {background, primary, secondary, third, fourth, start_point, end_point, graph_color, map_color}
                       Toutes les couleurs sont optionnelles
        """
        # Couleurs par défaut (actuelles du système)
        self._default_colors = {
            'background': '#F8F8F8',     # Arrière-plan clair
            'primary': '#FC4C02',        # Orange Strava principal (tracés, barres)
            'secondary': '#E74C3C',      # Rouge d'accentuation
            'third': '#3498DB',          # Bleu d'accentuation 2
            'fourth': '#34495E',         # Gris anthracite d'accentuation 3
            'start_point': '#22C55E',    # Vert (point de départ)
            'end_point': '#EF4444',      # Rouge (point d'arrivée)
            'graph_color': '#FC4C02',    # Couleur pour les graphiques (histogramme, profil d'élévation)
            'map_color': '#FC4C02'       # Couleur pour la carte (tracé GPS)
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
        valid_keys = {'background', 'primary', 'secondary', 'third', 'fourth', 'start_point', 'end_point', 'graph_color', 'map_color'}
        
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
    
    def get_background_color(self) -> str:
        """Couleur d'arrière-plan"""
        return self._custom_colors.get('background', self._default_colors['background'])
    
    def get_primary_color(self) -> str:
        """Couleur principale (tracés, barres d'histogramme)"""
        return self._custom_colors.get('primary', self._default_colors['primary'])
    
    def get_secondary_color(self) -> str:
        """Couleur secondaire d'accentuation"""
        return self._custom_colors.get('secondary', self._default_colors['secondary'])
    
    def get_third_color(self) -> str:
        """Couleur d'accentuation 2"""
        return self._custom_colors.get('third', self._default_colors['third'])
    
    def get_fourth_color(self) -> str:
        """Couleur d'accentuation 3 (axes, labels)"""
        return self._custom_colors.get('fourth', self._default_colors['fourth'])
    
    def get_start_point_color(self) -> str:
        """Couleur du point de départ"""
        return self._custom_colors.get('start_point', self._default_colors['start_point'])
    
    def get_end_point_color(self) -> str:
        """Couleur du point d'arrivée"""
        return self._custom_colors.get('end_point', self._default_colors['end_point'])
    
    def get_graph_color(self) -> str:
        """Couleur pour les graphiques (histogramme, profil d'élévation)"""
        return self._custom_colors.get('graph_color', self._default_colors['graph_color'])
    
    def get_map_color(self) -> str:
        """Couleur pour la carte (tracé GPS)"""
        return self._custom_colors.get('map_color', self._default_colors['map_color'])
    
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
            'COLOR_BACKGROUND': self.get_background_color(),
            'COLOR_PRIMARY': self.get_primary_color(),
            'COLOR_SECONDARY': self.get_secondary_color(),
            'COLOR_THIRD': self.get_third_color(),
            'COLOR_FOURTH': self.get_fourth_color(),
            'COLOR_START': self.get_start_point_color(),
            'COLOR_END': self.get_end_point_color(),
            'COLOR_STROKE': self.get_stroke_color(),
            'COLOR_GRAPH': self.get_graph_color(),
            'COLOR_MAP': self.get_map_color()
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


def create_custom_palette(background: Optional[str] = None,
                         primary: Optional[str] = None,
                         secondary: Optional[str] = None,
                         third: Optional[str] = None,
                         fourth: Optional[str] = None,
                         start_point: Optional[str] = None,
                         end_point: Optional[str] = None,
                         graph_color: Optional[str] = None,
                         map_color: Optional[str] = None) -> ColorPalette:
    """
    Crée une palette avec des couleurs personnalisées
    
    Args:
        background: Couleur d'arrière-plan
        primary: Couleur principale (tracés, barres)
        secondary: Couleur d'accentuation
        third: Couleur d'accentuation 2
        fourth: Couleur d'accentuation 3 (axes, labels)
        start_point: Couleur point de départ
        end_point: Couleur point d'arrivée
        graph_color: Couleur pour les graphiques (histogramme, profil d'élévation)
        map_color: Couleur pour la carte (tracé GPS)
        
    Returns:
        Palette de couleurs personnalisée
    """
    color_dict = {}
    
    if background:
        color_dict['background'] = background
    if primary:
        color_dict['primary'] = primary
    if secondary:
        color_dict['secondary'] = secondary
    if third:
        color_dict['third'] = third
    if fourth:
        color_dict['fourth'] = fourth
    if start_point:
        color_dict['start_point'] = start_point
    if end_point:
        color_dict['end_point'] = end_point
    if graph_color:
        color_dict['graph_color'] = graph_color
    if map_color:
        color_dict['map_color'] = map_color
    
    return ColorPalette(color_dict)