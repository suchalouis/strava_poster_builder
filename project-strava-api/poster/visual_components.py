"""
Composants visuels pour la génération de posters Strava
Contient les méthodes de génération des graphiques et visualisations
"""

from typing import Dict, Any, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class VisualComponents:
    """Générateur des composants visuels pour les posters Strava"""
    
    @staticmethod
    def create_pace_histogram_svg(activity_data: Dict[str, Any]) -> str:
        """
        Crée le contenu SVG de l'histogramme d'allure
        
        Args:
            activity_data: Données de l'activité avec km_splits
            
        Returns:
            Contenu SVG de l'histogramme ou chaîne vide si erreur
        """
        try:
            if not activity_data.get('km_splits'):
                return ""
            
            # Extraire les données des splits
            distances = []
            paces = []
            
            for split in activity_data['km_splits']:
                if split['pace_min_per_km'] > 0 and split['pace_min_per_km'] < 20:
                    distances.append(split['km'])
                    paces.append(split['pace_min_per_km'])
            
            if not paces:
                return ""
            
            def format_pace(pace_decimal):
                minutes = int(pace_decimal)
                seconds = int((pace_decimal - minutes) * 60)
                return f"{minutes}:{seconds:02d}"
            
            # Inverser les valeurs d'allure pour que vitesse plus élevée = barre plus haute
            max_pace = max(paces)
            inverted_paces = [(max_pace - pace + 1) for pace in paces]
            
            # Normaliser les hauteurs avec hauteur minimale garantie
            max_height = 35
            min_bar_height = 3
            usable_height = max_height - min_bar_height
            
            max_inverted = max(inverted_paces)
            min_inverted = min(inverted_paces)
            range_inverted = max_inverted - min_inverted
            
            if range_inverted > 0:
                normalized_heights = [min_bar_height + ((val - min_inverted) / range_inverted) * usable_height 
                                    for val in inverted_paces]
            else:
                normalized_heights = [max_height / 2] * len(inverted_paces)
            
            # Calculer les dimensions pour utiliser toute la largeur disponible
            available_width = 85  # 95 - 10 (5 de chaque côté)
            margin_left = 5
            
            spacing = 0.5
            total_spacing = (len(distances) - 1) * spacing if len(distances) > 1 else 0
            bar_width = (available_width - total_spacing) / len(distances) if len(distances) > 0 else available_width
            bar_width = min(bar_width, 8)
            
            total_bars_width = len(distances) * bar_width + total_spacing
            start_x = margin_left + (available_width - total_bars_width) / 2
            
            # Construire le SVG
            svg_content = f'<g id="pace-histogram" transform="translate({start_x}, 5)">\n'
            
            # Ajouter les barres
            for i, (pace, height) in enumerate(zip(paces, normalized_heights)):
                x = i * (bar_width + spacing)
                y = max_height - height
                
                svg_content += f'  <rect x="{x}" y="{y}" width="{bar_width}" height="{height}" '
                svg_content += f'fill="#FC4C02" stroke="#D63A02" stroke-width="0.2" opacity="0.9"/>\n'
            
            # Ajouter les labels de rythme
            label_y = max_height + 8
            for i, pace in enumerate(paces):
                x = i * (bar_width + spacing) + bar_width / 2
                svg_content += f'  <text x="{x}" y="{label_y}" '
                svg_content += f'font-family="Arial, sans-serif" font-size="2.5" font-weight="bold" '
                svg_content += f'fill="#333333" text-anchor="middle">{format_pace(pace)}</text>\n'
            
            svg_content += '</g>'
            return svg_content
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de l'histogramme d'allure: {e}")
            return ""
    
    @staticmethod
    def create_gps_map_svg(activity_data: Dict[str, Any]) -> str:
        """
        Crée le contenu SVG de la carte GPS
        
        Args:
            activity_data: Données de l'activité avec coordonnées
            
        Returns:
            Contenu SVG de la carte GPS
        """
        try:
            coordinates = activity_data.get('coordinates', [])
            
            if not coordinates or len(coordinates) < 2:
                return '<text x="85" y="60" font-family="Arial" font-size="3" fill="#999" text-anchor="middle">Pas de données GPS</text>'
            
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
            
            # Dimensions de la zone de carte (170x120 dans le template)
            map_width = 170
            map_height = 120
            margin = 10
            
            # Normaliser les coordonnées
            svg_points = []
            for lat, lon in coordinates:
                x = margin + ((lon - min_lon) / lon_range) * (map_width - 2 * margin)
                y = margin + ((max_lat - lat) / lat_range) * (map_height - 2 * margin)  # Inverser Y
                svg_points.append(f"{x:.2f},{y:.2f}")
            
            # Créer le tracé SVG
            path_data = "M " + " L ".join(svg_points)
            
            svg_content = f'''<g id="gps-track">
  <path d="{path_data}" 
        stroke="#FC4C02" stroke-width="1.5" fill="none" 
        stroke-linecap="round" stroke-linejoin="round" opacity="0.9"/>
  <circle cx="{svg_points[0].split(',')[0]}" cy="{svg_points[0].split(',')[1]}" 
          r="2" fill="#22C55E" stroke="white" stroke-width="0.5"/>
  <circle cx="{svg_points[-1].split(',')[0]}" cy="{svg_points[-1].split(',')[1]}" 
          r="2" fill="#EF4444" stroke="white" stroke-width="0.5"/>
</g>'''
            
            return svg_content
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de la carte GPS: {e}")
            return '<text x="85" y="60" font-family="Arial" font-size="3" fill="#999" text-anchor="middle">Erreur GPS</text>'
    
    @staticmethod
    def create_elevation_profile_svg(coordinates: List[Tuple[float, float, float]]) -> str:
        """
        Génère le profil d'altitude en SVG natif
        Zone disponible: 95x48 pixels
        
        Args:
            coordinates: Liste des coordonnées (lat, lon, altitude)
            
        Returns:
            Contenu SVG du profil d'altitude
        """
        try:
            if not coordinates or len(coordinates) < 2:
                return ''
            
            # Extraire les altitudes
            elevations = []
            distances = []
            total_distance = 0
            
            for i, coord in enumerate(coordinates):
                if len(coord) > 2 and coord[2] is not None:
                    elevations.append(coord[2])
                    if i == 0:
                        distances.append(0)
                    else:
                        # Distance euclidienne simple (approximation)
                        lat1, lon1 = coordinates[i-1][:2]
                        lat2, lon2 = coord[:2]
                        dist = ((lat2 - lat1) ** 2 + (lon2 - lon1) ** 2) ** 0.5 * 111000  # en mètres
                        total_distance += dist
                        distances.append(total_distance / 1000)  # en km
            
            if len(elevations) < 2:
                return ''
            
            # Normaliser les données pour s'adapter à la zone (95x48)
            min_elev = min(elevations)
            max_elev = max(elevations)
            max_dist = max(distances)
            
            # Éviter la division par zéro
            elev_range = max_elev - min_elev if max_elev != min_elev else 1
            
            # Générer les points du path SVG
            path_points = []
            for i, (dist, elev) in enumerate(zip(distances, elevations)):
                x = (dist / max_dist) * 95 if max_dist > 0 else 0
                y = 48 - ((elev - min_elev) / elev_range) * 48  # Inverser Y car SVG part du haut
                path_points.append((x, y))
            
            # Créer le path SVG pour la courbe
            path_data = f"M {path_points[0][0]:.1f} {path_points[0][1]:.1f}"
            for x, y in path_points[1:]:
                path_data += f" L {x:.1f} {y:.1f}"
            
            # Fermer le path pour le remplissage (aller au coin bas droit puis bas gauche)
            path_data += f" L 95 48 L 0 48 Z"
            
            # Générer le SVG
            svg_elements = [
                f'<path d="{path_data}" fill="#FC4C02" fill-opacity="0.3" stroke="#FC4C02" stroke-width="1"/>',
                f'<path d="{path_data[:-11]}" fill="none" stroke="#FC4C02" stroke-width="1.5"/>'  # Ligne sans remplissage
            ]
            
            return '\n'.join(svg_elements)
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du profil d'altitude: {e}")
            return ''
    
    @staticmethod 
    def create_gpx_track_svg(coordinates: List[Tuple[float, float, float]]) -> str:
        """
        Génère le tracé GPX en SVG natif (alternative à create_gps_map_svg)
        Zone disponible: 170x120 pixels
        
        Args:
            coordinates: Liste des coordonnées (lat, lon, altitude)
            
        Returns:
            Contenu SVG du tracé GPX
        """
        try:
            if not coordinates or len(coordinates) < 2:
                return ''
            
            # Extraire lat/lon
            lats = [coord[0] for coord in coordinates]
            lons = [coord[1] for coord in coordinates]
            
            # Calculer les limites
            min_lat, max_lat = min(lats), max(lats)
            min_lon, max_lon = min(lons), max(lons)
            
            # Éviter la division par zéro
            lat_range = max_lat - min_lat if max_lat != min_lat else 0.001
            lon_range = max_lon - min_lon if max_lon != min_lon else 0.001
            
            # Normaliser les coordonnées pour s'adapter à la zone (170x120)
            def normalize_coord(lat, lon):
                x = ((lon - min_lon) / lon_range) * 170
                y = ((max_lat - lat) / lat_range) * 120  # Inverser Y car SVG part du haut
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
            
            # Générer le SVG
            svg_elements = [
                f'<path d="{track_path}" fill="none" stroke="#FC4C02" stroke-width="2" stroke-linecap="round"/>',
                f'<circle cx="{start_x:.1f}" cy="{start_y:.1f}" r="3" fill="#00b894" stroke="white" stroke-width="1"/>',
                f'<circle cx="{end_x:.1f}" cy="{end_y:.1f}" r="3" fill="#d63031" stroke="white" stroke-width="1"/>'
            ]
            
            return '\n'.join(svg_elements)
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du tracé GPX: {e}")
            return ''