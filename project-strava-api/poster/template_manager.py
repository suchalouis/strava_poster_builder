"""
Module de gestion des templates SVG pour les posters Strava
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
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
    
    def extract_placeholder_dimensions(self) -> Dict[str, Dict[str, float]]:
        """
        Extrait les dimensions des zones de placeholders depuis le template SVG
        
        Returns:
            Dict avec les dimensions {placeholder: {"width": float, "height": float}}
        """
        try:
            template_content = self.get_template_content()
            dimensions = {}
            
            # Chercher les éléments <g> avec transform et contenant des placeholders
            g_pattern = r'<g[^>]*transform="translate\(([^,]+),\s*([^)]+)\)"[^>]*id="([^"]*)"[^>]*>(.*?){{(\w+)}}.*?</g>'
            g_matches = re.finditer(g_pattern, template_content, re.DOTALL)
            
            for match in g_matches:
                x_offset, y_offset, element_id, content, placeholder = match.groups()
                
                # Extraire les coordonnées de translation pour guider la recherche
                translate_x = float(x_offset)
                translate_y = float(y_offset)
                
                # Chercher tous les rectangles avant cet élément <g>
                g_start_pos = match.start()
                before_g_content = template_content[:g_start_pos]
                
                rect_pattern = r'<rect[^>]*x="([^"]*)"[^>]*y="([^"]*)"[^>]*width="([^"]*)"[^>]*height="([^"]*)"[^>]*/?>'
                rect_matches = list(re.finditer(rect_pattern, before_g_content))
                
                # Trouver le rectangle le plus proche géographiquement
                best_rect = None
                min_distance = float('inf')
                
                for rect_match in rect_matches:
                    rect_x, rect_y, width, height = rect_match.groups()
                    rect_x_val = float(rect_x)
                    rect_y_val = float(rect_y)
                    
                    # Calculer la distance entre le rect et la translation
                    distance = abs(rect_x_val - translate_x) + abs(rect_y_val - translate_y)
                    
                    if distance < min_distance:
                        min_distance = distance
                        best_rect = (rect_x, rect_y, width, height)
                
                if best_rect:
                    rect_x, rect_y, width, height = best_rect
                    dimensions[placeholder] = {
                        "width": float(width),
                        "height": float(height)
                    }
                    logger.debug(f"Dimensions extraites pour {placeholder}: {width}x{height}")
            
            # Méthode alternative : chercher directement les placeholders et les rect associés
            placeholder_pattern = r'{{(\w+)}}'
            placeholder_matches = list(re.finditer(placeholder_pattern, template_content))
            used_rects = set()  # Pour éviter de réutiliser les mêmes rectangles
            
            # Trier les matches pour traiter CUSTOM_GRAPH avant GPX_TRACK
            # (évite que GPX_TRACK prenne le rectangle de CUSTOM_GRAPH)
            placeholder_matches.sort(key=lambda m: (m.group(1) != 'CUSTOM_GRAPH', m.start()))
            
            for match in placeholder_matches:
                placeholder = match.group(1)
                if placeholder in dimensions:
                    continue  # Déjà trouvé avec la première méthode
                
                # Chercher un rect avant ce placeholder 
                # Pour GPX_TRACK, chercher plus loin car le rect peut être éloigné
                search_distance = 800 if placeholder == 'GPX_TRACK' else 300
                start_pos = max(0, match.start() - search_distance)
                context = template_content[start_pos:match.end()]
                
                # Chercher specifiquement les rect avec x, y, width, height dans l'ordre
                rect_pattern = r'<rect[^>]*x="([^"]*)"[^>]*y="([^"]*)"[^>]*width="([^"]*)"[^>]*height="([^"]*)"[^>]*/?>'
                rect_matches = list(re.finditer(rect_pattern, context))
                
                if rect_matches:
                    # Filtrer les rectangles déjà utilisés
                    available_rects = []
                    for rect_match in rect_matches:
                        rect_signature = rect_match.group(0)  # Le rect complet comme signature
                        if rect_signature not in used_rects:
                            available_rects.append(rect_match)
                    
                    if available_rects:
                        # Choisir le rectangle le plus approprié parmi ceux disponibles
                        if placeholder == 'GPX_TRACK' and len(available_rects) > 1:
                            # Pour GPX_TRACK, prendre celui avec les plus grandes dimensions
                            best_rect = None
                            max_area = 0
                            for rect_match in available_rects:
                                rect_x, rect_y, width, height = rect_match.groups()
                                area = float(width) * float(height)
                                if area > max_area:
                                    max_area = area
                                    best_rect = rect_match
                            chosen_rect = best_rect if best_rect else available_rects[-1]
                        else:
                            # Pour les autres, prendre le dernier disponible (le plus proche)
                            chosen_rect = available_rects[-1]
                        
                        rect_x, rect_y, width, height = chosen_rect.groups()
                        rect_signature = chosen_rect.group(0)
                        used_rects.add(rect_signature)  # Marquer comme utilisé
                        
                        dimensions[placeholder] = {
                            "width": float(width),
                            "height": float(height)
                        }
                        logger.debug(f"Dimensions extraites (méthode alternative) pour {placeholder}: {width}x{height}")
                else:
                    # Si pas de rect trouvé, chercher width et height séparément
                    width_pattern = r'width="([^"]*)"'
                    height_pattern = r'height="([^"]*)"'
                    
                    width_matches = list(re.finditer(width_pattern, context))
                    height_matches = list(re.finditer(height_pattern, context))
                    
                    if width_matches and height_matches:
                        # Prendre les derniers trouvés
                        width = width_matches[-1].group(1)
                        height = height_matches[-1].group(1)
                        dimensions[placeholder] = {
                            "width": float(width),
                            "height": float(height)
                        }
                        logger.debug(f"Dimensions extraites (width/height séparés) pour {placeholder}: {width}x{height}")
            
            # Valeurs par défaut pour les placeholders connus si non trouvés
            default_dimensions = {
                "CUSTOM_GRAPH": {"width": 95.0, "height": 48.0},
                "GPX_TRACK": {"width": 170.0, "height": 120.0},
                "ELEVATION_PROFILE": {"width": 95.0, "height": 48.0}
            }
            
            for placeholder, default_dims in default_dimensions.items():
                if placeholder not in dimensions:
                    dimensions[placeholder] = default_dims
                    logger.debug(f"Dimensions par défaut utilisées pour {placeholder}: {default_dims['width']}x{default_dims['height']}")
            
            logger.info(f"Dimensions extraites pour {len(dimensions)} placeholders")
            return dimensions
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des dimensions: {e}")
            # Retourner les dimensions par défaut en cas d'erreur
            return {
                "CUSTOM_GRAPH": {"width": 95.0, "height": 48.0},
                "GPX_TRACK": {"width": 170.0, "height": 120.0},
                "ELEVATION_PROFILE": {"width": 95.0, "height": 48.0}
            }