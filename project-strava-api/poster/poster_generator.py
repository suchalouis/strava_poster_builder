"""
Générateur de posters unifié pour les activités Strava
Combine les fonctionnalités des anciens générateurs en une API cohérente
"""

from typing import Dict, Any, Optional
from pathlib import Path
import logging

from .template_manager import TemplateManager
from .visual_components import VisualComponents
from .formatters import DataFormatters

logger = logging.getLogger(__name__)


class PosterGenerator:
    """
    Générateur unifié de posters SVG pour les activités Strava
    
    Cette classe centralise toutes les fonctionnalités de génération de posters:
    - Gestion des templates SVG
    - Génération des composants visuels (histogramme, carte GPS, profil d'altitude)
    - Formatage des données d'activité
    - Assemblage final du poster
    """
    
    def __init__(self, template_path: Optional[str] = None):
        """
        Initialise le générateur de posters
        
        Args:
            template_path: Chemin vers le template SVG (optionnel)
        """
        self.template_manager = TemplateManager(template_path)
        self.visual_components = VisualComponents()
        self.formatters = DataFormatters()
    
    def generate_poster(self, activity_data: Dict[str, Any]) -> str:
        """
        Génère un poster SVG complet pour une activité
        
        Args:
            activity_data: Données de l'activité Strava
            
        Returns:
            Contenu SVG du poster généré
            
        Raises:
            RuntimeError: En cas d'erreur lors de la génération
        """
        try:
            logger.info(f"Génération du poster pour l'activité: {activity_data.get('name', 'Unknown')}")
            
            # 1. Formater les données de base
            replacements = self.formatters.create_poster_replacements(activity_data)
            
            # 2. Générer les composants visuels
            visual_components = self._generate_visual_components(activity_data)
            
            # 3. Ajouter les composants visuels aux remplacements
            replacements.update(visual_components)
            
            # 4. Créer le contenu SVG final
            poster_content = self.template_manager.create_poster_content(replacements)
            
            logger.info("Poster généré avec succès")
            return poster_content
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du poster: {e}")
            raise RuntimeError(f"Échec de la génération du poster: {e}")
    
    def _generate_visual_components(self, activity_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Génère tous les composants visuels pour l'activité
        
        Args:
            activity_data: Données de l'activité
            
        Returns:
            Dict des composants visuels générés
        """
        components = {}
        
        # Extraire les dimensions des placeholders depuis le template
        try:
            placeholder_dimensions = self.template_manager.extract_placeholder_dimensions()
            logger.debug(f"Dimensions extraites du template: {placeholder_dimensions}")
        except Exception as e:
            logger.warning(f"Erreur lors de l'extraction des dimensions: {e}")
            placeholder_dimensions = {}
        
        # Histogramme d'allure (splits km)
        if activity_data.get('km_splits'):
            try:
                custom_graph_dims = placeholder_dimensions.get('CUSTOM_GRAPH')
                pace_histogram = self.visual_components.create_pace_histogram_svg(activity_data, custom_graph_dims)
                components['CUSTOM_GRAPH'] = pace_histogram
                components['PACE_HISTOGRAM'] = pace_histogram  # Alias alternatif
            except Exception as e:
                logger.warning(f"Erreur lors de la génération de l'histogramme d'allure: {e}")
                components['CUSTOM_GRAPH'] = ""
                components['PACE_HISTOGRAM'] = ""
        else:
            components['CUSTOM_GRAPH'] = ""
            components['PACE_HISTOGRAM'] = ""
        
        # Carte GPS / Tracé GPX
        if activity_data.get('coordinates'):
            try:
                gpx_track_dims = placeholder_dimensions.get('GPX_TRACK')
                
                # Utiliser la méthode principale pour la carte GPS
                gps_map = self.visual_components.create_gps_map_svg(activity_data, gpx_track_dims)
                components['GPX_TRACK'] = gps_map
                components['GPS_MAP'] = gps_map  # Alias alternatif
                
                # Alternative avec tracé GPX (pour compatibilité)
                coordinates_with_elevation = activity_data['coordinates']
                if len(coordinates_with_elevation[0]) >= 3:
                    gpx_track = self.visual_components.create_gpx_track_svg(coordinates_with_elevation, gpx_track_dims)
                    components['GPX_TRACK_ALT'] = gpx_track
                else:
                    components['GPX_TRACK_ALT'] = gps_map
                    
            except Exception as e:
                logger.warning(f"Erreur lors de la génération de la carte GPS: {e}")
                # Utiliser les dimensions pour les messages d'erreur
                if gpx_track_dims:
                    center_x = gpx_track_dims.get('width', 170.0) / 2
                    center_y = gpx_track_dims.get('height', 120.0) / 2
                else:
                    center_x, center_y = 85, 60
                error_text = f'<text x="{center_x}" y="{center_y}" font-family="Arial" font-size="3" fill="#999" text-anchor="middle">Erreur GPS</text>'
                components['GPX_TRACK'] = error_text
                components['GPS_MAP'] = error_text
                components['GPX_TRACK_ALT'] = ""
        else:
            # Utiliser les dimensions pour les messages de fallback
            gpx_track_dims = placeholder_dimensions.get('GPX_TRACK')
            if gpx_track_dims:
                center_x = gpx_track_dims.get('width', 170.0) / 2
                center_y = gpx_track_dims.get('height', 120.0) / 2
            else:
                center_x, center_y = 85, 60
            no_data_text = f'<text x="{center_x}" y="{center_y}" font-family="Arial" font-size="3" fill="#999" text-anchor="middle">Pas de données GPS</text>'
            components['GPX_TRACK'] = no_data_text
            components['GPS_MAP'] = no_data_text
            components['GPX_TRACK_ALT'] = ""
        
        # Profil d'altitude
        coordinates = activity_data.get('coordinates', [])
        if coordinates and len(coordinates) > 0 and len(coordinates[0]) >= 3:
            try:
                elevation_dims = placeholder_dimensions.get('ELEVATION_PROFILE')
                elevation_profile = self.visual_components.create_elevation_profile_svg(coordinates, elevation_dims)
                components['ELEVATION_PROFILE'] = elevation_profile
            except Exception as e:
                logger.warning(f"Erreur lors de la génération du profil d'altitude: {e}")
                components['ELEVATION_PROFILE'] = ""
        else:
            components['ELEVATION_PROFILE'] = ""
        
        return components
    
    def save_poster(self, activity_data: Dict[str, Any], output_path: str) -> str:
        """
        Génère et sauvegarde un poster SVG
        
        Args:
            activity_data: Données de l'activité
            output_path: Chemin de sortie pour le fichier SVG
            
        Returns:
            Chemin du fichier sauvegardé
        """
        poster_content = self.generate_poster(activity_data)
        
        # S'assurer que le répertoire parent existe
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarder le contenu
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(poster_content)
        
        logger.info(f"Poster sauvegardé: {output_path}")
        return str(output_file)
    
    def get_template_path(self) -> Path:
        """
        Récupère le chemin du template actuellement utilisé
        
        Returns:
            Chemin du template SVG
        """
        return self.template_manager.template_path
    
    def reload_template(self) -> None:
        """
        Recharge le template SVG depuis le fichier
        Utile lors du développement ou si le template a été modifié
        """
        self.template_manager.reload_template()
        logger.info("Template SVG rechargé")
    
    def validate_activity_data(self, activity_data: Dict[str, Any]) -> bool:
        """
        Valide que les données d'activité contiennent les éléments minimum requis
        
        Args:
            activity_data: Données de l'activité à valider
            
        Returns:
            True si les données sont valides, False sinon
        """
        required_fields = ['name']  # Champs absolument requis
        optional_fields = ['distance', 'moving_time', 'type', 'coordinates', 'km_splits']
        
        # Vérifier les champs requis
        for field in required_fields:
            if field not in activity_data:
                logger.warning(f"Champ requis manquant: {field}")
                return False
        
        # Avertir pour les champs optionnels manquants
        missing_optional = [field for field in optional_fields if field not in activity_data]
        if missing_optional:
            logger.info(f"Champs optionnels manquants (poster sera limité): {missing_optional}")
        
        return True
    
    def get_poster_info(self, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Récupère des informations sur le poster qui sera généré
        
        Args:
            activity_data: Données de l'activité
            
        Returns:
            Dict avec les informations du poster
        """
        has_pace_data = bool(activity_data.get('km_splits'))
        has_gps_data = bool(activity_data.get('coordinates'))
        has_elevation_data = bool(activity_data.get('coordinates') and 
                                 len(activity_data['coordinates']) > 0 and 
                                 len(activity_data['coordinates'][0]) >= 3)
        
        return {
            'activity_name': activity_data.get('name', 'Unknown'),
            'activity_type': activity_data.get('type', 'Unknown'),
            'has_pace_histogram': has_pace_data,
            'has_gps_track': has_gps_data,
            'has_elevation_profile': has_elevation_data,
            'template_path': str(self.template_manager.template_path),
            'is_valid': self.validate_activity_data(activity_data)
        }