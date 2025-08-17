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
    def create_pace_histogram_svg(activity_data: Dict[str, Any], dimensions: Optional[Dict[str, float]] = None) -> str:
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
            
            # Utiliser les dimensions fournies ou les valeurs par défaut
            if dimensions:
                available_width = dimensions.get('width', 95.0)
                max_height = dimensions.get('height', 48.0)
            else:
                available_width = 95.0
                max_height = 48.0
            
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
                total_seconds = round(pace_decimal * 60)
                minutes = total_seconds // 60
                seconds = total_seconds % 60
                return f"{minutes}:{seconds:02d}"
            
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
            svg_content += f'  <line x1="{y_axis_x}" y1="0" x2="{y_axis_x}" y2="{chart_height}" '
            svg_content += f'stroke="#333333" stroke-width="0.5"/>\n'
            
            # Ajouter les ticks et labels de l'axe Y
            for i, tick_pace in enumerate(y_ticks):
                if min_pace <= tick_pace <= max_pace:
                    # Calculer la position Y du tick (aligné avec la logique d'inversion des barres)
                    tick_y = ((tick_pace - min_pace) / (max_pace - min_pace)) * chart_height
                    
                    # Ligne du tick
                    svg_content += f'  <line x1="{y_axis_x - 1}" y1="{tick_y}" x2="{y_axis_x + 1}" y2="{tick_y}" '
                    svg_content += f'stroke="#333333" stroke-width="0.5"/>\n'
                    
                    # Label du tick - utiliser les secondes exactes pour le formatage
                    tick_seconds = y_ticks_seconds[i]
                    tick_minutes = tick_seconds // 60
                    tick_secs = tick_seconds % 60
                    pace_label = f"{tick_minutes}:{tick_secs:02d}"
                    
                    svg_content += f'  <text x="{y_axis_x - 3}" y="{tick_y + 1}" '
                    svg_content += f'font-family="Arial, sans-serif" font-size="2" font-weight="normal" '
                    svg_content += f'fill="#333333" text-anchor="end">{pace_label}</text>\n'
            
            # Ajouter les barres (ajustées pour la nouvelle position)
            bars_start_x = start_x - 5  # Compenser le translate initial
            for i, height in enumerate(normalized_heights):
                x = bars_start_x + i * (bar_width + spacing)
                y = chart_height - height
                
                svg_content += f'  <rect x="{x}" y="{y}" width="{bar_width}" height="{height}" '
                svg_content += f'fill="#FC4C02" stroke="#D63A02" stroke-width="0.2" opacity="0.9"/>\n'
            
            svg_content += '</g>'
            return svg_content
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de l'histogramme d'allure: {e}")
            return ""
    
    @staticmethod
    def create_gps_map_svg(activity_data: Dict[str, Any], dimensions: Optional[Dict[str, float]] = None) -> str:
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
            
            # Utiliser les dimensions fournies ou les valeurs par défaut
            if dimensions:
                map_width = dimensions.get('width', 170.0)
                map_height = dimensions.get('height', 120.0)
            else:
                map_width = 170.0
                map_height = 120.0
            
            center_x = map_width / 2
            center_y = map_height / 2
            
            if not coordinates or len(coordinates) < 2:
                return f'<text x="{center_x}" y="{center_y}" font-family="Arial" font-size="3" fill="#999" text-anchor="middle">Pas de données GPS</text>'
            
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
            
            svg_content = f'''<g id="gps-track">
  <path d="{path_data}" 
        stroke="#FC4C02" stroke-width="{stroke_width}" fill="none" 
        stroke-linecap="round" stroke-linejoin="round" opacity="0.9"/>
  <circle cx="{svg_points[0].split(',')[0]}" cy="{svg_points[0].split(',')[1]}" 
          r="{circle_radius}" fill="#22C55E" stroke="white" stroke-width="0.5"/>
  <circle cx="{svg_points[-1].split(',')[0]}" cy="{svg_points[-1].split(',')[1]}" 
          r="{circle_radius}" fill="#EF4444" stroke="white" stroke-width="0.5"/>
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
            return f'<text x="{center_x}" y="{center_y}" font-family="Arial" font-size="3" fill="#999" text-anchor="middle">Erreur GPS</text>'
    
    @staticmethod
    def create_elevation_profile_svg(coordinates: List[Tuple[float, float, float]], dimensions: Optional[Dict[str, float]] = None) -> str:
        """
        Génère le profil d'altitude en SVG natif
        
        Args:
            coordinates: Liste des coordonnées (lat, lon, altitude)
            dimensions: Dict optionnel avec width et height pour la zone disponible
            
        Returns:
            Contenu SVG du profil d'altitude
        """
        try:
            if not coordinates or len(coordinates) < 2:
                return ''
            
            # Utiliser les dimensions fournies ou les valeurs par défaut
            if dimensions:
                profile_width = dimensions.get('width', 95.0)
                profile_height = dimensions.get('height', 48.0)
            else:
                profile_width = 95.0
                profile_height = 48.0
            
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
            
            # Normaliser les données pour s'adapter à la zone
            min_elev = min(elevations)
            max_elev = max(elevations)
            max_dist = max(distances)
            
            # Éviter la division par zéro
            elev_range = max_elev - min_elev if max_elev != min_elev else 1
            
            # Générer les points du path SVG
            path_points = []
            for i, (dist, elev) in enumerate(zip(distances, elevations)):
                x = (dist / max_dist) * profile_width if max_dist > 0 else 0
                y = profile_height - ((elev - min_elev) / elev_range) * profile_height  # Inverser Y car SVG part du haut
                path_points.append((x, y))
            
            # Créer le path SVG pour la courbe
            path_data = f"M {path_points[0][0]:.1f} {path_points[0][1]:.1f}"
            for x, y in path_points[1:]:
                path_data += f" L {x:.1f} {y:.1f}"
            
            # Fermer le path pour le remplissage (aller au coin bas droit puis bas gauche)
            path_data += f" L {profile_width} {profile_height} L 0 {profile_height} Z"
            
            # Utiliser des épaisseurs proportionnelles
            stroke_width_fill = max(1, min(profile_width, profile_height) * 0.02)
            stroke_width_line = max(1.5, min(profile_width, profile_height) * 0.03)
            
            # Générer le SVG
            svg_elements = [
                f'<path d="{path_data}" fill="#FC4C02" fill-opacity="0.3" stroke="#FC4C02" stroke-width="{stroke_width_fill}"/>',
                f'<path d="{path_data[:-len(f" L {profile_width} {profile_height} L 0 {profile_height} Z")]}" fill="none" stroke="#FC4C02" stroke-width="{stroke_width_line}"/>'  # Ligne sans remplissage
            ]
            
            return '\n'.join(svg_elements)
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du profil d'altitude: {e}")
            return ''
    
    @staticmethod 
    def create_gpx_track_svg(coordinates: List[Tuple[float, float, float]], dimensions: Optional[Dict[str, float]] = None) -> str:
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
            
            # Utiliser les dimensions fournies ou les valeurs par défaut
            if dimensions:
                track_width = dimensions.get('width', 170.0)
                track_height = dimensions.get('height', 120.0)
            else:
                track_width = 170.0
                track_height = 120.0
            
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
            
            # Générer le SVG
            svg_elements = [
                f'<path d="{track_path}" fill="none" stroke="#FC4C02" stroke-width="{stroke_width}" stroke-linecap="round"/>',
                f'<circle cx="{start_x:.1f}" cy="{start_y:.1f}" r="{circle_radius}" fill="#00b894" stroke="white" stroke-width="{circle_stroke}"/>',
                f'<circle cx="{end_x:.1f}" cy="{end_y:.1f}" r="{circle_radius}" fill="#d63031" stroke="white" stroke-width="{circle_stroke}"/>'
            ]
            
            return '\n'.join(svg_elements)
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du tracé GPX: {e}")
            return ''