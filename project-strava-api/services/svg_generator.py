"""
Générateur SVG pour les posters Strava
"""

from typing import Dict, Any, List, Tuple
from pathlib import Path


class SVGGenerator:
    """Générateur SVG pour les posters avec système de placeholders"""
    
    def __init__(self, template_path: str, debug_background: bool = True):
        self.template_path = template_path
        self.debug_background = debug_background
        
    def load_template(self) -> str:
        """Charger le template SVG comme string"""
        with open(self.template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def generate_elevation_profile_svg(self, coordinates: List[Tuple[float, float, float]]) -> str:
        """
        Générer le profil d'altitude en SVG natif
        Zone disponible: 95x48 pixels
        """
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
    
    def generate_gpx_track_svg(self, coordinates: List[Tuple[float, float, float]]) -> str:
        """
        Générer le tracé GPX en SVG natif
        Zone disponible: 170x120 pixels
        """
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
    
    def replace_placeholders(self, svg_content: str, activity_data: Dict[str, Any]) -> str:
        """
        Remplacer les placeholders dans le template SVG
        """
        # Générer le profil d'altitude et le tracé GPX
        coordinates = activity_data.get('coordinates', [])
        elevation_svg = self.generate_elevation_profile_svg(coordinates)
        gpx_track_svg = self.generate_gpx_track_svg(coordinates)
        
        # Mapping des données vers les placeholders
        replacements = {
            '{{ACTIVITY_NAME}}': str(activity_data.get('name', 'Activité Strava')),
            '{{DURATION}}': str(activity_data.get('moving_time', 0)),
            '{{DISTANCE}}': str(activity_data.get('distance', 0)),
            '{{ACTIVITY_TYPE}}': str(activity_data.get('type', 'Unknown')),
            '{{ELEVATION_GAIN}}': str(activity_data.get('total_elevation_gain', 0)),
            '{{ELEVATION_PROFILE}}': elevation_svg,
            '{{GPX_TRACK}}': gpx_track_svg
        }
        
        # Remplacer tous les placeholders
        result = svg_content
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, value)
        
        return result
    
    def generate_poster(self, activity_data: Dict[str, Any]) -> str:
        """
        Générer le poster complet avec le nouveau système de placeholders
        """
        # Charger le template
        svg_content = self.load_template()
        
        # Remplacer les placeholders
        final_svg = self.replace_placeholders(svg_content, activity_data)
        
        return final_svg
    
    def save_svg(self, activity_data: Dict[str, Any], output_path: str) -> str:
        """
        Sauvegarder le poster en SVG
        """
        svg_content = self.generate_poster(activity_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
            
        return output_path