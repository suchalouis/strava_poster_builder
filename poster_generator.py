#!/usr/bin/env python3
"""
Module commun pour la génération de posters Strava
Centralise le code partagé entre test_poster_with_real_data.py et test_svg_generation.py
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple


class PosterGenerator:
    """Générateur de posters SVG pour les activités Strava"""
    
    def __init__(self, template_path: str = "poster_framework.svg"):
        """
        Initialise le générateur
        
        Args:
            template_path: Chemin vers le template SVG
        """
        self.template_path = template_path
        self.template_content = None
        self._load_template()
    
    def _load_template(self):
        """Charge le template SVG"""
        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"Template SVG non trouvé: {self.template_path}")
        
        with open(self.template_path, 'r', encoding='utf-8') as f:
            self.template_content = f.read()
    
    def format_activity_statistics(self, activity_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Formate les statistiques de l'activité pour l'affichage
        
        Args:
            activity_data: Données de l'activité
            
        Returns:
            Dict avec les statistiques formatées
        """
        distance_km = activity_data.get('distance', 0) / 1000
        duration_s = activity_data.get('moving_time', 0)
        duration_formatted = f"{duration_s // 3600}h{(duration_s % 3600) // 60:02d}m"
        
        elevation_gain = activity_data.get('total_elevation_gain', 0)
        activity_type = activity_data.get('type', 'Activité')
        
        return {
            'ACTIVITY_NAME': activity_data.get('name', 'Activité Strava'),
            'DISTANCE': f"{distance_km:.1f} km",
            'DURATION': duration_formatted,
            'ELEVATION_GAIN': f"{elevation_gain:.0f} m" if elevation_gain else "-- m",
            'ACTIVITY_TYPE': activity_type
        }
    
    def create_pace_histogram_svg(self, activity_data: Dict[str, Any]) -> str:
        """
        Crée le contenu SVG de l'histogramme d'allure
        
        Args:
            activity_data: Données de l'activité avec km_splits
            
        Returns:
            Contenu SVG de l'histogramme ou chaîne vide si erreur
        """
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
            normalized_heights = [min_bar_height + ((val - min_inverted) / range_inverted) * usable_height for val in inverted_paces]
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
    
    def create_gps_map_svg(self, activity_data: Dict[str, Any]) -> str:
        """
        Crée le contenu SVG de la carte GPS
        
        Args:
            activity_data: Données de l'activité avec coordonnées
            
        Returns:
            Contenu SVG de la carte GPS
        """
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
    
    def generate_poster(self, activity_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """
        Génère un poster SVG complet
        
        Args:
            activity_data: Données de l'activité
            output_path: Chemin de sortie (optionnel)
            
        Returns:
            Chemin du fichier généré
        """
        if not self.template_content:
            raise RuntimeError("Template SVG non chargé")
        
        # Formater les statistiques
        stats = self.format_activity_statistics(activity_data)
        
        # Générer l'histogramme d'allure
        pace_histogram = self.create_pace_histogram_svg(activity_data)
        
        # Générer la carte GPS
        gps_map = self.create_gps_map_svg(activity_data)
        
        # Remplacer les placeholders
        poster_content = self.template_content
        for key, value in stats.items():
            poster_content = poster_content.replace(f'{{{{{key}}}}}', value)
        
        poster_content = poster_content.replace('{{CUSTOM_GRAPH}}', pace_histogram)
        poster_content = poster_content.replace('{{GPX_TRACK}}', gps_map)
        
        # Déterminer le chemin de sortie
        if not output_path:
            safe_name = stats['ACTIVITY_NAME'].replace(' ', '_').replace('/', '_')[:20]
            output_path = f"poster_{safe_name}.svg"
        
        # Sauvegarder
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(poster_content)
        
        return output_path


def load_strava_test_data(data_file: str = 'test_strava_data.json') -> Optional[Tuple[Dict, List[Dict]]]:
    """
    Charge les données de test Strava
    
    Args:
        data_file: Chemin vers le fichier de données
        
    Returns:
        Tuple (user_data, activities_data) ou None si erreur
    """
    if not os.path.exists(data_file):
        print(f"❌ Fichier {data_file} non trouvé")
        print("   Exécute d'abord: python collect_test_data_oauth.py")
        return None
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        user_data = data['user_data']
        activities_data = data['activities_data']
        
        return user_data, activities_data
        
    except Exception as e:
        print(f"❌ Erreur lors du chargement des données: {e}")
        return None


def get_first_activity_with_splits(activities_data: List[Dict]) -> Optional[Dict]:
    """
    Récupère la première activité avec des splits km
    
    Args:
        activities_data: Liste des activités
        
    Returns:
        Première activité avec splits ou None
    """
    for activity in activities_data:
        if activity.get('km_splits'):
            return activity
    return None