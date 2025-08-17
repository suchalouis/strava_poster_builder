"""
Composants visuels pour la génération de posters Strava
Contient les méthodes de génération des graphiques et visualisations
"""

from typing import Dict, Any, List, Tuple, Optional
import logging
import math
import base64
import io
import requests
from PIL import Image, ImageDraw
from .color_palette import ColorPalette, create_default_palette

logger = logging.getLogger(__name__)


class VisualComponents:
    """Générateur des composants visuels pour les posters Strava"""
    
    def __init__(self, color_palette: Optional[ColorPalette] = None):
        """
        Initialise les composants visuels avec une palette de couleurs
        
        Args:
            color_palette: Palette de couleurs à utiliser (optionnel)
        """
        self.color_palette = color_palette or create_default_palette()
    
    def calculate_responsive_dimensions(self, template_dimensions: Dict[str, float], 
                                      original_width: float, 
                                      original_height: float) -> Dict[str, float]:
        """
        Calcule les dimensions responsives en conservant le ratio d'aspect original
        
        Args:
            template_dimensions: Dimensions de la zone disponible dans le template
            original_width: Largeur originale du graphique
            original_height: Hauteur originale du graphique
            
        Returns:
            Dict avec les nouvelles dimensions {"width": float, "height": float}
        """
        if not template_dimensions:
            return {"width": original_width, "height": original_height}
        
        max_width = template_dimensions.get('width', original_width)
        max_height = template_dimensions.get('height', original_height)
        
        # Calculer le ratio d'aspect original
        original_ratio = original_width / original_height if original_height > 0 else 1.0
        
        # Calculer les dimensions en fonction des contraintes
        # Calculer les ratios de redimensionnement pour chaque dimension
        width_scale = max_width / original_width
        height_scale = max_height / original_height
        
        # Utiliser le plus petit ratio pour conserver les proportions
        # Autoriser l'agrandissement en retirant la limite de 1.0
        scale = min(width_scale, height_scale)
        
        # Appliquer le redimensionnement
        new_width = original_width * scale
        new_height = original_height * scale
        
        # Éviter les dimensions nulles ou négatives tout en conservant le ratio
        min_dimension = 10.0
        if new_width < min_dimension or new_height < min_dimension:
            # Si une dimension est trop petite, redimensionner en conservant le ratio
            if new_width < new_height:
                # Largeur limitante
                new_width = min_dimension
                new_height = min_dimension / original_ratio
            else:
                # Hauteur limitante
                new_height = min_dimension
                new_width = min_dimension * original_ratio
        
        logger.debug(f"Dimensions responsives: {original_width}x{original_height} → {new_width:.1f}x{new_height:.1f}")
        
        return {"width": new_width, "height": new_height}
    
    def create_pace_histogram_svg(self, activity_data: Dict[str, Any], dimensions: Optional[Dict[str, float]] = None) -> str:
        """
        Crée le contenu SVG de l'histogramme d'allure
        
        Args:
            activity_data: Données de l'activité avec km_splits
            dimensions: Dict optionnel avec width et height pour la zone disponible
            
        Returns:
            Contenu SVG de l'histogramme ou chaîne vide si erreur
        """
        try:
            if not activity_data.get('km_splits'):
                return ""
            
            # Dimensions originales par défaut de l'histogramme d'allure
            original_width = 95.0
            original_height = 48.0
            
            # Calculer les dimensions responsives
            responsive_dims = self.calculate_responsive_dimensions(
                dimensions, original_width, original_height
            )
            
            available_width = responsive_dims['width']
            max_height = responsive_dims['height']
            
            # Extraire les données des splits
            distances = []
            paces = []
            
            for split in activity_data['km_splits']:
                if split['pace_min_per_km'] > 0 and split['pace_min_per_km'] < 20:
                    distances.append(split['km'])
                    paces.append(split['pace_min_per_km'])
            
            if not paces:
                return ""
            
            # Inverser les valeurs d'allure pour que vitesse plus élevée = barre plus haute
            max_pace = max(paces)
            inverted_paces = [(max_pace - pace + 1) for pace in paces]
            
            # Normaliser les hauteurs avec hauteur minimale garantie (proportionnelle)
            chart_height = max_height - 10  # Réserver de l'espace pour les marges
            min_bar_height = max(3, chart_height * 0.08)  # Minimum 8% de la hauteur
            usable_height = chart_height - min_bar_height
            
            max_inverted = max(inverted_paces)
            min_inverted = min(inverted_paces)
            range_inverted = max_inverted - min_inverted
            
            if range_inverted > 0:
                normalized_heights = [min_bar_height + ((val - min_inverted) / range_inverted) * usable_height 
                                    for val in inverted_paces]
            else:
                normalized_heights = [chart_height / 2] * len(inverted_paces)
            
            # Calculer les dimensions pour utiliser toute la largeur disponible en tenant compte de l'axe Y
            y_axis_margin = max(15, available_width * 0.15)  # Proportionnel à la largeur
            chart_width = available_width - y_axis_margin - 10  # 10 pour marges générales
            margin_left = 5 + y_axis_margin
            
            spacing = max(0.5, chart_width * 0.01)  # Proportionnel à la largeur
            total_spacing = (len(distances) - 1) * spacing if len(distances) > 1 else 0
            bar_width = (chart_width - total_spacing) / len(distances) if len(distances) > 0 else chart_width
            bar_width = min(bar_width, max(8, chart_width * 0.1))  # Max 10% de la largeur
            
            total_bars_width = len(distances) * bar_width + total_spacing
            start_x = margin_left + (chart_width - total_bars_width) / 2
            
            # Calculer les valeurs de l'axe Y (allures en intervalles de 10 secondes)
            min_pace = min(paces)
            max_pace = max(paces)
            
            # Convertir en secondes totales avec arrondi approprié
            min_pace_seconds = round(min_pace * 60)
            max_pace_seconds = round(max_pace * 60)
            
            # Ajuster aux intervalles de 10 secondes
            min_y_seconds = (min_pace_seconds // 10) * 10
            max_y_seconds = ((max_pace_seconds // 10) + 1) * 10
            
            # Créer les ticks de l'axe Y en secondes exactes
            y_ticks_seconds = []
            current_seconds = min_y_seconds
            while current_seconds <= max_y_seconds:
                y_ticks_seconds.append(current_seconds)
                current_seconds += 10
            
            # Convertir en valeurs décimales pour les calculs de position
            y_ticks = [seconds / 60.0 for seconds in y_ticks_seconds]
            
            # Construire le SVG
            svg_content = f'<g id="pace-histogram" transform="translate({5}, 5)">\n'
            
            # Ajouter l'axe Y
            y_axis_x = y_axis_margin - 2
            axis_color = self.color_palette.get_fourth_color()
            svg_content += f'  <line x1="{y_axis_x}" y1="0" x2="{y_axis_x}" y2="{chart_height}" '
            svg_content += f'stroke="{axis_color}" stroke-width="0.5"/>\n'
            
            # Ajouter les ticks et labels de l'axe Y
            for i, tick_pace in enumerate(y_ticks):
                if min_pace <= tick_pace <= max_pace:
                    # Calculer la position Y du tick (aligné avec la logique d'inversion des barres)
                    tick_y = ((tick_pace - min_pace) / (max_pace - min_pace)) * chart_height
                    
                    # Ligne du tick
                    svg_content += f'  <line x1="{y_axis_x - 1}" y1="{tick_y}" x2="{y_axis_x + 1}" y2="{tick_y}" '
                    svg_content += f'stroke="{axis_color}" stroke-width="0.5"/>\n'
                    
                    # Label du tick - utiliser les secondes exactes pour le formatage
                    tick_seconds = y_ticks_seconds[i]
                    tick_minutes = tick_seconds // 60
                    tick_secs = tick_seconds % 60
                    pace_label = f"{tick_minutes}:{tick_secs:02d}"
                    
                    svg_content += f'  <text x="{y_axis_x - 3}" y="{tick_y + 1}" '
                    svg_content += f'font-family="Arial, sans-serif" font-size="2" font-weight="normal" '
                    svg_content += f'fill="{axis_color}" text-anchor="end">{pace_label}</text>\n'
            
            # Ajouter les barres (ajustées pour la nouvelle position)
            bars_start_x = start_x - 5  # Compenser le translate initial
            for i, height in enumerate(normalized_heights):
                x = bars_start_x + i * (bar_width + spacing)
                y = chart_height - height
                
                graph_color = self.color_palette.get_graph_color()
                stroke_color = self.color_palette.get_stroke_color()
                svg_content += f'  <rect x="{x}" y="{y}" width="{bar_width}" height="{height}" '
                svg_content += f'fill="{graph_color}" stroke="{stroke_color}" stroke-width="0.2" opacity="0.9"/>\n'
            
            svg_content += '</g>'
            return svg_content
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de l'histogramme d'allure: {e}")
            return ""
    
    def create_gps_map_svg(self, activity_data: Dict[str, Any], dimensions: Optional[Dict[str, float]] = None) -> str:
        """
        Crée le contenu SVG de la carte GPS
        
        Args:
            activity_data: Données de l'activité avec coordonnées
            dimensions: Dict optionnel avec width et height pour la zone disponible
            
        Returns:
            Contenu SVG de la carte GPS
        """
        try:
            coordinates = activity_data.get('coordinates', [])
            
            # Dimensions originales par défaut de la carte GPS
            original_width = 170.0
            original_height = 120.0
            
            # Calculer les dimensions responsives
            responsive_dims = self.calculate_responsive_dimensions(
                dimensions, original_width, original_height
            )
            
            map_width = responsive_dims['width']
            map_height = responsive_dims['height']
            
            center_x = map_width / 2
            center_y = map_height / 2
            
            if not coordinates or len(coordinates) < 2:
                error_color = self.color_palette.get_fourth_color()
                return f'<text x="{center_x}" y="{center_y}" font-family="Arial" font-size="3" fill="{error_color}" text-anchor="middle">Pas de données GPS</text>'
            
            # Calculer les limites géographiques
            lats = [coord[0] for coord in coordinates]
            lons = [coord[1] for coord in coordinates]
            
            min_lat, max_lat = min(lats), max(lats)
            min_lon, max_lon = min(lons), max(lons)
            
            # Éviter la division par zéro
            lat_range = max_lat - min_lat
            lon_range = max_lon - min_lon
            
            if lat_range == 0:
                lat_range = 0.001
            if lon_range == 0:
                lon_range = 0.001
            
            # Utiliser une marge proportionnelle
            margin = min(10, min(map_width, map_height) * 0.08)  # 8% de la plus petite dimension
            
            # Normaliser les coordonnées
            svg_points = []
            for lat, lon in coordinates:
                x = margin + ((lon - min_lon) / lon_range) * (map_width - 2 * margin)
                y = margin + ((max_lat - lat) / lat_range) * (map_height - 2 * margin)  # Inverser Y
                svg_points.append(f"{x:.2f},{y:.2f}")
            
            # Créer le tracé SVG avec épaisseur proportionnelle
            path_data = "M " + " L ".join(svg_points)
            stroke_width = max(1.5, min(map_width, map_height) * 0.012)  # Proportionnel à la taille
            circle_radius = max(2, min(map_width, map_height) * 0.015)  # Proportionnel à la taille
            
            # Utiliser les couleurs de la palette
            map_color = self.color_palette.get_map_color()
            start_color = self.color_palette.get_start_point_color()
            end_color = self.color_palette.get_end_point_color()
            
            svg_content = f'''<g id="gps-track">
  <path d="{path_data}" 
        stroke="{map_color}" stroke-width="{stroke_width}" fill="none" 
        stroke-linecap="round" stroke-linejoin="round" opacity="0.9"/>
  <circle cx="{svg_points[0].split(',')[0]}" cy="{svg_points[0].split(',')[1]}" 
          r="{circle_radius}" fill="{start_color}" stroke="white" stroke-width="0.5"/>
  <circle cx="{svg_points[-1].split(',')[0]}" cy="{svg_points[-1].split(',')[1]}" 
          r="{circle_radius}" fill="{end_color}" stroke="white" stroke-width="0.5"/>
</g>'''
            
            return svg_content
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de la carte GPS: {e}")
            # Utiliser les dimensions pour centrer le message d'erreur
            if dimensions:
                center_x = dimensions.get('width', 170.0) / 2
                center_y = dimensions.get('height', 120.0) / 2
            else:
                center_x, center_y = 85, 60
            error_color = self.color_palette.get_fourth_color()
            return f'<text x="{center_x}" y="{center_y}" font-family="Arial" font-size="3" fill="{error_color}" text-anchor="middle">Erreur GPS</text>'
    
    def create_elevation_profile_svg(self, coordinates: List[Tuple[float, float, float]], dimensions: Optional[Dict[str, float]] = None) -> str:
        """
        Génère le tracé GPX en conservant le ratio d'aspect et l'orientation nord
        
        Args:
            coordinates: Liste des coordonnées (lat, lon, altitude)
            dimensions: Dict optionnel avec width et height pour la zone disponible
            
        Returns:
            Contenu SVG du tracé GPX avec ratio conservé
        """
        try:
            if not coordinates or len(coordinates) < 2:
                return ''
            
            # Extraire lat/lon
            lats = [coord[0] for coord in coordinates]
            lons = [coord[1] for coord in coordinates]
            
            # Calculer les limites géographiques
            min_lat, max_lat = min(lats), max(lats)
            min_lon, max_lon = min(lons), max(lons)
            
            # Éviter la division par zéro
            lat_range = max_lat - min_lat if max_lat != min_lat else 0.001
            lon_range = max_lon - min_lon if max_lon != min_lon else 0.001
            
            # Calculer le ratio d'aspect du tracé (comme une image)
            track_aspect_ratio = lon_range / lat_range
            
            # Créer des dimensions "originales" basées sur le ratio du tracé
            # Utiliser une taille de référence arbitraire
            reference_height = 100.0
            original_width = reference_height * track_aspect_ratio
            original_height = reference_height
            
            # Calculer les dimensions responsives en conservant le ratio
            responsive_dims = self.calculate_responsive_dimensions(
                dimensions, original_width, original_height
            )
            
            track_width = responsive_dims['width']
            track_height = responsive_dims['height']
            
            # Calculer les marges pour centrer le tracé
            available_width = dimensions.get('width', track_width) if dimensions else track_width
            available_height = dimensions.get('height', track_height) if dimensions else track_height
            
            margin_x = (available_width - track_width) / 2
            margin_y = (available_height - track_height) / 2
            
            # Normaliser les coordonnées en conservant l'orientation nord (lat élevée = haut)
            def normalize_coord(lat, lon):
                x = ((lon - min_lon) / lon_range) * track_width
                y = ((max_lat - lat) / lat_range) * track_height  # Nord vers le haut
                return x, y
            
            # Créer le tracé principal
            path_data = []
            for i, (lat, lon) in enumerate(zip(lats, lons)):
                x, y = normalize_coord(lat, lon)
                if i == 0:
                    path_data.append(f"M {x:.1f} {y:.1f}")
                else:
                    path_data.append(f"L {x:.1f} {y:.1f}")
            
            track_path = ' '.join(path_data)
            
            # Points de départ et d'arrivée
            start_x, start_y = normalize_coord(lats[0], lons[0])
            end_x, end_y = normalize_coord(lats[-1], lons[-1])
            
            # Utiliser des épaisseurs proportionnelles
            stroke_width = max(2, min(track_width, track_height) * 0.016)
            circle_radius = max(3, min(track_width, track_height) * 0.025)
            circle_stroke = max(1, min(track_width, track_height) * 0.008)
            
            # Utiliser les couleurs de la palette
            map_color = self.color_palette.get_map_color()
            start_color = self.color_palette.get_start_point_color()
            end_color = self.color_palette.get_end_point_color()
            
            # Générer le SVG avec centrage
            svg_elements = [
                f'<g transform="translate({margin_x:.1f}, {margin_y:.1f})">',
                f'  <path d="{track_path}" fill="none" stroke="{map_color}" stroke-width="{stroke_width}" stroke-linecap="round"/>',
                f'  <circle cx="{start_x:.1f}" cy="{start_y:.1f}" r="{circle_radius}" fill="{start_color}" stroke="white" stroke-width="{circle_stroke}"/>',
                f'  <circle cx="{end_x:.1f}" cy="{end_y:.1f}" r="{circle_radius}" fill="{end_color}" stroke="white" stroke-width="{circle_stroke}"/>',
                '</g>'
            ]
            
            return '\n'.join(svg_elements)
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du tracé GPX: {e}")
            return ''
    
    def _deg_to_tile(self, lat: float, lon: float, zoom: int) -> Tuple[int, int]:
        """
        Convertit des coordonnées lat/lon en numéros de tuile OSM
        
        Args:
            lat: Latitude en degrés
            lon: Longitude en degrés
            zoom: Niveau de zoom OSM
            
        Returns:
            Tuple (x, y) des coordonnées de tuile
        """
        lat_rad = math.radians(lat)
        n = 2.0 ** zoom
        x = int((lon + 180.0) / 360.0 * n)
        y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return x, y
    
    def _tile_to_deg(self, x: int, y: int, zoom: int) -> Tuple[float, float]:
        """
        Convertit des coordonnées de tuile OSM en lat/lon
        
        Args:
            x: Coordonnée X de tuile
            y: Coordonnée Y de tuile
            zoom: Niveau de zoom OSM
            
        Returns:
            Tuple (lat, lon) en degrés
        """
        n = 2.0 ** zoom
        lon = x / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
        lat = math.degrees(lat_rad)
        return lat, lon
    
    def _fetch_osm_tile(self, x: int, y: int, zoom: int, timeout: int = 10) -> Optional[Image.Image]:
        """
        Récupère une tuile de carte OSM
        
        Args:
            x: Coordonnée X de tuile
            y: Coordonnée Y de tuile  
            zoom: Niveau de zoom OSM
            timeout: Timeout pour la requête HTTP
            
        Returns:
            Image PIL de la tuile ou None si erreur
        """
        try:
            # Utiliser le serveur de tuiles OSM standard
            url = f"https://tile.openstreetmap.org/{zoom}/{x}/{y}.png"
            
            # Headers pour être respectueux de l'API OSM
            headers = {
                'User-Agent': 'Strava-Poster-Builder/1.0 (Educational use)'
            }
            
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            # Convertir en image PIL
            return Image.open(io.BytesIO(response.content))
            
        except Exception as e:
            logger.warning(f"Erreur lors de la récupération de la tuile OSM {x},{y},{zoom}: {e}")
            return None
    
    def create_gpx_osm_overlay_svg(self, coordinates: List[Tuple[float, float, float]], 
                                   dimensions: Optional[Dict[str, float]] = None,
                                   zoom_level: int = 14) -> str:
        """
        Génère un SVG avec le tracé GPX superposé sur une carte OpenStreetMap
        
        Args:
            coordinates: Liste des coordonnées (lat, lon, altitude)
            dimensions: Dict optionnel avec width et height pour la zone disponible
            zoom_level: Niveau de zoom OSM (défaut: 14)
            
        Returns:
            Contenu SVG avec carte OSM et tracé GPX superposé
        """
        try:
            if not coordinates or len(coordinates) < 2:
                return ''
            
            # Dimensions par défaut
            default_width = 400.0
            default_height = 300.0
            
            # Calculer les dimensions responsives
            if dimensions:
                map_width = dimensions.get('width', default_width)
                map_height = dimensions.get('height', default_height)
            else:
                map_width = default_width
                map_height = default_height
            
            # Extraire lat/lon
            lats = [coord[0] for coord in coordinates]
            lons = [coord[1] for coord in coordinates]
            
            # Calculer les limites du tracé
            min_lat, max_lat = min(lats), max(lats)
            min_lon, max_lon = min(lons), max(lons)
            
            # Calculer le centre du tracé
            center_lat = (min_lat + max_lat) / 2
            center_lon = (min_lon + max_lon) / 2
            
            # Calculer les tuiles nécessaires pour couvrir la zone
            # Ajouter une marge pour s'assurer que tout le tracé est visible
            margin_factor = 1.2
            lat_range = (max_lat - min_lat) * margin_factor
            lon_range = (max_lon - min_lon) * margin_factor
            
            # Déterminer la zone de tuiles
            top_lat = center_lat + lat_range / 2
            bottom_lat = center_lat - lat_range / 2
            left_lon = center_lon - lon_range / 2
            right_lon = center_lon + lon_range / 2
            
            # Convertir en coordonnées de tuiles
            left_tile_x, top_tile_y = self._deg_to_tile(top_lat, left_lon, zoom_level)
            right_tile_x, bottom_tile_y = self._deg_to_tile(bottom_lat, right_lon, zoom_level)
            
            # S'assurer qu'on a au moins une tuile
            tile_width = max(1, right_tile_x - left_tile_x + 1)
            tile_height = max(1, bottom_tile_y - top_tile_y + 1)
            
            logger.info(f"Zone de tuiles: {tile_width}x{tile_height} tuiles (zoom {zoom_level})")
            
            # Limiter le nombre de tuiles pour éviter les requêtes excessives
            max_tiles = 16  # 4x4 maximum
            if tile_width * tile_height > max_tiles:
                logger.warning(f"Trop de tuiles nécessaires ({tile_width}x{tile_height}), limitation à {max_tiles}")
                # Réduire la zone ou augmenter le zoom
                if tile_width > tile_height:
                    tile_width = min(tile_width, 4)
                    tile_height = min(tile_height, max_tiles // tile_width)
                else:
                    tile_height = min(tile_height, 4)
                    tile_width = min(tile_width, max_tiles // tile_height)
            
            # Créer l'image composite
            tile_size = 256  # Taille standard des tuiles OSM
            map_image_width = tile_width * tile_size
            map_image_height = tile_height * tile_size
            
            # Créer une image de base
            composite_image = Image.new('RGB', (map_image_width, map_image_height), (200, 200, 200))
            
            # Récupérer et assembler les tuiles
            tiles_fetched = 0
            for tile_y in range(top_tile_y, top_tile_y + tile_height):
                for tile_x in range(left_tile_x, left_tile_x + tile_width):
                    tile_image = self._fetch_osm_tile(tile_x, tile_y, zoom_level)
                    if tile_image:
                        paste_x = (tile_x - left_tile_x) * tile_size
                        paste_y = (tile_y - top_tile_y) * tile_size
                        composite_image.paste(tile_image, (paste_x, paste_y))
                        tiles_fetched += 1
            
            logger.info(f"Tuiles récupérées: {tiles_fetched}/{tile_width * tile_height}")
            
            # Redimensionner l'image composite aux dimensions souhaitées
            composite_image = composite_image.resize((int(map_width), int(map_height)), Image.Resampling.LANCZOS)
            
            # Calculer les coordonnées du tracé sur l'image
            # Convertir les coordonnées géographiques en coordonnées pixel
            def coord_to_pixel(lat: float, lon: float) -> Tuple[float, float]:
                # Convertir en coordonnées de tuile fractionnaires
                tile_x_frac = (lon + 180.0) / 360.0 * (2 ** zoom_level)
                lat_rad = math.radians(lat)
                tile_y_frac = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * (2 ** zoom_level)
                
                # Convertir en coordonnées pixel relatives à notre zone
                pixel_x = (tile_x_frac - left_tile_x) * tile_size
                pixel_y = (tile_y_frac - top_tile_y) * tile_size
                
                # Redimensionner aux dimensions finales
                final_x = pixel_x * map_width / map_image_width
                final_y = pixel_y * map_height / map_image_height
                
                return final_x, final_y
            
            # Créer le tracé GPX en SVG
            path_points = []
            for lat, lon in zip(lats, lons):
                x, y = coord_to_pixel(lat, lon)
                path_points.append((x, y))
            
            # Générer le path SVG pour le tracé
            if path_points:
                path_data = f"M {path_points[0][0]:.1f} {path_points[0][1]:.1f}"
                for x, y in path_points[1:]:
                    path_data += f" L {x:.1f} {y:.1f}"
                
                # Points de départ et d'arrivée
                start_x, start_y = path_points[0]
                end_x, end_y = path_points[-1]
                
                # Épaisseurs proportionnelles
                stroke_width = max(3, min(map_width, map_height) * 0.01)
                circle_radius = max(4, min(map_width, map_height) * 0.015)
                
                # Convertir l'image en base64 pour l'inclure dans le SVG
                img_buffer = io.BytesIO()
                composite_image.save(img_buffer, format='PNG')
                img_b64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
                
                # Générer le SVG avec image de fond et tracé
                svg_elements = [
                    f'<g id="gpx-osm-overlay">',
                    f'  <!-- Carte OSM de fond (zoom {zoom_level}, {tiles_fetched} tuiles) -->',
                    f'  <image x="0" y="0" width="{map_width}" height="{map_height}" href="data:image/png;base64,{img_b64}"/>',
                    f'  <!-- Tracé GPX superposé -->',
                    f'  <path d="{path_data}" fill="none" stroke="{self.color_palette.get_map_color()}" stroke-width="{stroke_width}" stroke-linecap="round" opacity="0.9"/>',
                    f'  <circle cx="{start_x:.1f}" cy="{start_y:.1f}" r="{circle_radius}" fill="{self.color_palette.get_start_point_color()}" stroke="white" stroke-width="2"/>',
                    f'  <circle cx="{end_x:.1f}" cy="{end_y:.1f}" r="{circle_radius}" fill="{self.color_palette.get_end_point_color()}" stroke="white" stroke-width="2"/>',
                    '</g>'
                ]
                
                return '\n'.join(svg_elements)
            else:
                return ''
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du tracé GPX sur carte OSM: {e}")
            # Fallback vers un tracé simple en cas d'erreur
            return self.create_elevation_profile_svg(coordinates, dimensions)
    
    def create_elevation_profile_svg_mercator(self, coordinates: List[Tuple[float, float, float]], dimensions: Optional[Dict[str, float]] = None) -> str:
        """
        Génère le tracé GPX avec correction de Mercator pour un ratio géographique réel
        
        Args:
            coordinates: Liste des coordonnées (lat, lon, altitude)
            dimensions: Dict optionnel avec width et height pour la zone disponible
            
        Returns:
            Contenu SVG du tracé GPX avec correction géographique de Mercator
        """
        try:
            if not coordinates or len(coordinates) < 2:
                return ''
            
            # Extraire lat/lon
            lats = [coord[0] for coord in coordinates]
            lons = [coord[1] for coord in coordinates]
            
            # Calculer les limites géographiques
            min_lat, max_lat = min(lats), max(lats)
            min_lon, max_lon = min(lons), max(lons)
            
            # Éviter la division par zéro
            lat_range = max_lat - min_lat if max_lat != min_lat else 0.001
            lon_range = max_lon - min_lon if max_lon != min_lon else 0.001
            
            # Calculer la latitude moyenne pour la correction de Mercator
            lat_moyenne = (min_lat + max_lat) / 2
            lat_moyenne_rad = math.radians(lat_moyenne)
            
            # Appliquer la correction de Mercator
            # Les degrés de longitude représentent une distance plus courte aux latitudes élevées
            lon_range_corrected = lon_range * math.cos(lat_moyenne_rad)
            
            # Calculer le ratio d'aspect géographique corrigé
            track_aspect_ratio = lon_range_corrected / lat_range
            
            # Créer des dimensions "originales" basées sur le ratio géographique corrigé
            reference_height = 100.0
            original_width = reference_height * track_aspect_ratio
            original_height = reference_height
            
            # Calculer les dimensions responsives en conservant le ratio géographique
            responsive_dims = self.calculate_responsive_dimensions(
                dimensions, original_width, original_height
            )
            
            track_width = responsive_dims['width']
            track_height = responsive_dims['height']
            
            # Calculer les marges pour centrer le tracé
            available_width = dimensions.get('width', track_width) if dimensions else track_width
            available_height = dimensions.get('height', track_height) if dimensions else track_height
            
            margin_x = (available_width - track_width) / 2
            margin_y = (available_height - track_height) / 2
            
            # Normaliser les coordonnées en conservant l'orientation nord (lat élevée = haut)
            def normalize_coord(lat, lon):
                x = ((lon - min_lon) / lon_range) * track_width
                y = ((max_lat - lat) / lat_range) * track_height  # Nord vers le haut
                return x, y
            
            # Créer le tracé principal
            path_data = []
            for i, (lat, lon) in enumerate(zip(lats, lons)):
                x, y = normalize_coord(lat, lon)
                if i == 0:
                    path_data.append(f"M {x:.1f} {y:.1f}")
                else:
                    path_data.append(f"L {x:.1f} {y:.1f}")
            
            track_path = ' '.join(path_data)
            
            # Points de départ et d'arrivée
            start_x, start_y = normalize_coord(lats[0], lons[0])
            end_x, end_y = normalize_coord(lats[-1], lons[-1])
            
            # Utiliser des épaisseurs proportionnelles
            stroke_width = max(2, min(track_width, track_height) * 0.016)
            circle_radius = max(3, min(track_width, track_height) * 0.025)
            circle_stroke = max(1, min(track_width, track_height) * 0.008)
            
            # Utiliser les couleurs de la palette
            map_color = self.color_palette.get_map_color()
            start_color = self.color_palette.get_start_point_color()
            end_color = self.color_palette.get_end_point_color()
            
            # Générer le SVG avec centrage
            svg_elements = [
                f'<g transform="translate({margin_x:.1f}, {margin_y:.1f})">',
                f'  <!-- Tracé GPX avec correction Mercator (lat_moy={lat_moyenne:.2f}°, ratio_geo={track_aspect_ratio:.2f}) -->',
                f'  <path d="{track_path}" fill="none" stroke="{map_color}" stroke-width="{stroke_width}" stroke-linecap="round"/>',
                f'  <circle cx="{start_x:.1f}" cy="{start_y:.1f}" r="{circle_radius}" fill="{start_color}" stroke="white" stroke-width="{circle_stroke}"/>',
                f'  <circle cx="{end_x:.1f}" cy="{end_y:.1f}" r="{circle_radius}" fill="{end_color}" stroke="white" stroke-width="{circle_stroke}"/>',
                '</g>'
            ]
            
            return '\n'.join(svg_elements)
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du tracé GPX avec correction Mercator: {e}")
            return ''
    
    def create_gpx_track_svg(self, coordinates: List[Tuple[float, float, float]], dimensions: Optional[Dict[str, float]] = None) -> str:
        """
        Génère le tracé GPX en SVG natif (alternative à create_gps_map_svg)
        
        Args:
            coordinates: Liste des coordonnées (lat, lon, altitude)
            dimensions: Dict optionnel avec width et height pour la zone disponible
            
        Returns:
            Contenu SVG du tracé GPX
        """
        try:
            if not coordinates or len(coordinates) < 2:
                return ''
            
            # Dimensions originales par défaut du tracé GPX
            original_width = 170.0
            original_height = 120.0
            
            # Calculer les dimensions responsives
            responsive_dims = self.calculate_responsive_dimensions(
                dimensions, original_width, original_height
            )
            
            track_width = responsive_dims['width']
            track_height = responsive_dims['height']
            
            # Extraire lat/lon
            lats = [coord[0] for coord in coordinates]
            lons = [coord[1] for coord in coordinates]
            
            # Calculer les limites
            min_lat, max_lat = min(lats), max(lats)
            min_lon, max_lon = min(lons), max(lons)
            
            # Éviter la division par zéro
            lat_range = max_lat - min_lat if max_lat != min_lat else 0.001
            lon_range = max_lon - min_lon if max_lon != min_lon else 0.001
            
            # Normaliser les coordonnées pour s'adapter à la zone
            def normalize_coord(lat, lon):
                x = ((lon - min_lon) / lon_range) * track_width
                y = ((max_lat - lat) / lat_range) * track_height  # Inverser Y car SVG part du haut
                return x, y
            
            # Créer le tracé principal
            path_data = []
            for i, (lat, lon) in enumerate(zip(lats, lons)):
                x, y = normalize_coord(lat, lon)
                if i == 0:
                    path_data.append(f"M {x:.1f} {y:.1f}")
                else:
                    path_data.append(f"L {x:.1f} {y:.1f}")
            
            track_path = ' '.join(path_data)
            
            # Points de départ et d'arrivée
            start_x, start_y = normalize_coord(lats[0], lons[0])
            end_x, end_y = normalize_coord(lats[-1], lons[-1])
            
            # Utiliser des épaisseurs proportionnelles
            stroke_width = max(2, min(track_width, track_height) * 0.016)
            circle_radius = max(3, min(track_width, track_height) * 0.025)
            circle_stroke = max(1, min(track_width, track_height) * 0.008)
            
            # Utiliser les couleurs de la palette
            map_color = self.color_palette.get_map_color()
            start_color = self.color_palette.get_start_point_color()
            end_color = self.color_palette.get_end_point_color()
            
            # Générer le SVG
            svg_elements = [
                f'<path d="{track_path}" fill="none" stroke="{map_color}" stroke-width="{stroke_width}" stroke-linecap="round"/>',
                f'<circle cx="{start_x:.1f}" cy="{start_y:.1f}" r="{circle_radius}" fill="{start_color}" stroke="white" stroke-width="{circle_stroke}"/>',
                f'<circle cx="{end_x:.1f}" cy="{end_y:.1f}" r="{circle_radius}" fill="{end_color}" stroke="white" stroke-width="{circle_stroke}"/>'
            ]
            
            return '\n'.join(svg_elements)
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du tracé GPX: {e}")
            return ''
    
    def _deg_to_tile(self, lat: float, lon: float, zoom: int) -> Tuple[int, int]:
        """
        Convertit des coordonnées lat/lon en numéros de tuile OSM
        
        Args:
            lat: Latitude en degrés
            lon: Longitude en degrés
            zoom: Niveau de zoom OSM
            
        Returns:
            Tuple (x, y) des coordonnées de tuile
        """
        lat_rad = math.radians(lat)
        n = 2.0 ** zoom
        x = int((lon + 180.0) / 360.0 * n)
        y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return x, y
    
    def _tile_to_deg(self, x: int, y: int, zoom: int) -> Tuple[float, float]:
        """
        Convertit des coordonnées de tuile OSM en lat/lon
        
        Args:
            x: Coordonnée X de tuile
            y: Coordonnée Y de tuile
            zoom: Niveau de zoom OSM
            
        Returns:
            Tuple (lat, lon) en degrés
        """
        n = 2.0 ** zoom
        lon = x / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
        lat = math.degrees(lat_rad)
        return lat, lon
    
    def _fetch_osm_tile(self, x: int, y: int, zoom: int, timeout: int = 10) -> Optional[Image.Image]:
        """
        Récupère une tuile de carte OSM
        
        Args:
            x: Coordonnée X de tuile
            y: Coordonnée Y de tuile  
            zoom: Niveau de zoom OSM
            timeout: Timeout pour la requête HTTP
            
        Returns:
            Image PIL de la tuile ou None si erreur
        """
        try:
            # Utiliser le serveur de tuiles OSM standard
            url = f"https://tile.openstreetmap.org/{zoom}/{x}/{y}.png"
            
            # Headers pour être respectueux de l'API OSM
            headers = {
                'User-Agent': 'Strava-Poster-Builder/1.0 (Educational use)'
            }
            
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            # Convertir en image PIL
            return Image.open(io.BytesIO(response.content))
            
        except Exception as e:
            logger.warning(f"Erreur lors de la récupération de la tuile OSM {x},{y},{zoom}: {e}")
            return None
    
    def create_gpx_osm_overlay_svg(self, coordinates: List[Tuple[float, float, float]], 
                                   dimensions: Optional[Dict[str, float]] = None,
                                   zoom_level: int = 14) -> str:
        """
        Génère un SVG avec le tracé GPX superposé sur une carte OpenStreetMap
        
        Args:
            coordinates: Liste des coordonnées (lat, lon, altitude)
            dimensions: Dict optionnel avec width et height pour la zone disponible
            zoom_level: Niveau de zoom OSM (défaut: 14)
            
        Returns:
            Contenu SVG avec carte OSM et tracé GPX superposé
        """
        try:
            if not coordinates or len(coordinates) < 2:
                return ''
            
            # Dimensions par défaut
            default_width = 400.0
            default_height = 300.0
            
            # Calculer les dimensions responsives
            if dimensions:
                map_width = dimensions.get('width', default_width)
                map_height = dimensions.get('height', default_height)
            else:
                map_width = default_width
                map_height = default_height
            
            # Extraire lat/lon
            lats = [coord[0] for coord in coordinates]
            lons = [coord[1] for coord in coordinates]
            
            # Calculer les limites du tracé
            min_lat, max_lat = min(lats), max(lats)
            min_lon, max_lon = min(lons), max(lons)
            
            # Calculer le centre du tracé
            center_lat = (min_lat + max_lat) / 2
            center_lon = (min_lon + max_lon) / 2
            
            # Calculer les tuiles nécessaires pour couvrir la zone
            # Ajouter une marge pour s'assurer que tout le tracé est visible
            margin_factor = 1.2
            lat_range = (max_lat - min_lat) * margin_factor
            lon_range = (max_lon - min_lon) * margin_factor
            
            # Déterminer la zone de tuiles
            top_lat = center_lat + lat_range / 2
            bottom_lat = center_lat - lat_range / 2
            left_lon = center_lon - lon_range / 2
            right_lon = center_lon + lon_range / 2
            
            # Convertir en coordonnées de tuiles
            left_tile_x, top_tile_y = self._deg_to_tile(top_lat, left_lon, zoom_level)
            right_tile_x, bottom_tile_y = self._deg_to_tile(bottom_lat, right_lon, zoom_level)
            
            # S'assurer qu'on a au moins une tuile
            tile_width = max(1, right_tile_x - left_tile_x + 1)
            tile_height = max(1, bottom_tile_y - top_tile_y + 1)
            
            logger.info(f"Zone de tuiles: {tile_width}x{tile_height} tuiles (zoom {zoom_level})")
            
            # Limiter le nombre de tuiles pour éviter les requêtes excessives
            max_tiles = 16  # 4x4 maximum
            if tile_width * tile_height > max_tiles:
                logger.warning(f"Trop de tuiles nécessaires ({tile_width}x{tile_height}), limitation à {max_tiles}")
                # Réduire la zone ou augmenter le zoom
                if tile_width > tile_height:
                    tile_width = min(tile_width, 4)
                    tile_height = min(tile_height, max_tiles // tile_width)
                else:
                    tile_height = min(tile_height, 4)
                    tile_width = min(tile_width, max_tiles // tile_height)
            
            # Créer l'image composite
            tile_size = 256  # Taille standard des tuiles OSM
            map_image_width = tile_width * tile_size
            map_image_height = tile_height * tile_size
            
            # Créer une image de base
            composite_image = Image.new('RGB', (map_image_width, map_image_height), (200, 200, 200))
            
            # Récupérer et assembler les tuiles
            tiles_fetched = 0
            for tile_y in range(top_tile_y, top_tile_y + tile_height):
                for tile_x in range(left_tile_x, left_tile_x + tile_width):
                    tile_image = self._fetch_osm_tile(tile_x, tile_y, zoom_level)
                    if tile_image:
                        paste_x = (tile_x - left_tile_x) * tile_size
                        paste_y = (tile_y - top_tile_y) * tile_size
                        composite_image.paste(tile_image, (paste_x, paste_y))
                        tiles_fetched += 1
            
            logger.info(f"Tuiles récupérées: {tiles_fetched}/{tile_width * tile_height}")
            
            # Redimensionner l'image composite aux dimensions souhaitées
            composite_image = composite_image.resize((int(map_width), int(map_height)), Image.Resampling.LANCZOS)
            
            # Calculer les coordonnées du tracé sur l'image
            # Convertir les coordonnées géographiques en coordonnées pixel
            def coord_to_pixel(lat: float, lon: float) -> Tuple[float, float]:
                # Convertir en coordonnées de tuile fractionnaires
                tile_x_frac = (lon + 180.0) / 360.0 * (2 ** zoom_level)
                lat_rad = math.radians(lat)
                tile_y_frac = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * (2 ** zoom_level)
                
                # Convertir en coordonnées pixel relatives à notre zone
                pixel_x = (tile_x_frac - left_tile_x) * tile_size
                pixel_y = (tile_y_frac - top_tile_y) * tile_size
                
                # Redimensionner aux dimensions finales
                final_x = pixel_x * map_width / map_image_width
                final_y = pixel_y * map_height / map_image_height
                
                return final_x, final_y
            
            # Créer le tracé GPX en SVG
            path_points = []
            for lat, lon in zip(lats, lons):
                x, y = coord_to_pixel(lat, lon)
                path_points.append((x, y))
            
            # Générer le path SVG pour le tracé
            if path_points:
                path_data = f"M {path_points[0][0]:.1f} {path_points[0][1]:.1f}"
                for x, y in path_points[1:]:
                    path_data += f" L {x:.1f} {y:.1f}"
                
                # Points de départ et d'arrivée
                start_x, start_y = path_points[0]
                end_x, end_y = path_points[-1]
                
                # Épaisseurs proportionnelles
                stroke_width = max(3, min(map_width, map_height) * 0.01)
                circle_radius = max(4, min(map_width, map_height) * 0.015)
                
                # Convertir l'image en base64 pour l'inclure dans le SVG
                img_buffer = io.BytesIO()
                composite_image.save(img_buffer, format='PNG')
                img_b64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
                
                # Générer le SVG avec image de fond et tracé
                svg_elements = [
                    f'<g id="gpx-osm-overlay">',
                    f'  <!-- Carte OSM de fond (zoom {zoom_level}, {tiles_fetched} tuiles) -->',
                    f'  <image x="0" y="0" width="{map_width}" height="{map_height}" href="data:image/png;base64,{img_b64}"/>',
                    f'  <!-- Tracé GPX superposé -->',
                    f'  <path d="{path_data}" fill="none" stroke="{self.color_palette.get_map_color()}" stroke-width="{stroke_width}" stroke-linecap="round" opacity="0.9"/>',
                    f'  <circle cx="{start_x:.1f}" cy="{start_y:.1f}" r="{circle_radius}" fill="{self.color_palette.get_start_point_color()}" stroke="white" stroke-width="2"/>',
                    f'  <circle cx="{end_x:.1f}" cy="{end_y:.1f}" r="{circle_radius}" fill="{self.color_palette.get_end_point_color()}" stroke="white" stroke-width="2"/>',
                    '</g>'
                ]
                
                return '\n'.join(svg_elements)
            else:
                return ''
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du tracé GPX sur carte OSM: {e}")
            # Fallback vers un tracé simple en cas d'erreur
            return self.create_elevation_profile_svg(coordinates, dimensions)