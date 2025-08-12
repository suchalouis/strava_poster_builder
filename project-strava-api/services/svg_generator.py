"""
Générateur SVG pour les posters Strava
"""

import io
import base64
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from xml.etree import ElementTree as ET
import numpy as np


class SVGGenerator:
    """Générateur de widgets SVG pour les posters"""
    
    def __init__(self, template_path: str):
        self.template_path = template_path
        self.svg_tree = None
        self.svg_root = None
        
    def load_template(self) -> None:
        """Charger le template SVG"""
        self.svg_tree = ET.parse(self.template_path)
        self.svg_root = self.svg_tree.getroot()
        
    def generate_stats_widget(self, activity_data: Dict[str, Any]) -> None:
        """
        Générer le widget des statistiques
        Position: widget-stats (x=5, y=35, w=66.67, h=50)
        """
        # Extraire les stats
        distance_km = activity_data.get('distance', 0) / 1000
        moving_time = activity_data.get('moving_time', 0)
        elevation_gain = activity_data.get('total_elevation_gain', 0)
        avg_speed = activity_data.get('average_speed', 0) * 3.6  # m/s vers km/h
        
        # Convertir le temps en format h:min
        hours = moving_time // 3600
        minutes = (moving_time % 3600) // 60
        time_str = f"{hours}h{minutes:02d}" if hours > 0 else f"{minutes}min"
        
        # Créer le groupe de texte pour les stats
        stats_group = ET.Element('{http://www.w3.org/2000/svg}g')
        stats_group.set('id', 'stats-content')
        
        # Style pour les textes de stats
        stats_style = {
            'font-family': 'Arial, sans-serif',
            'font-size': '3.5mm',
            'fill': '#333333',
            'text-anchor': 'start'
        }
        
        label_style = {
            'font-family': 'Arial, sans-serif',
            'font-size': '2.5mm',
            'fill': '#666666',
            'text-anchor': 'start'
        }
        
        # Position de base du widget stats
        base_x = 8
        base_y = 42
        
        # Distance
        dist_label = ET.SubElement(stats_group, '{http://www.w3.org/2000/svg}text')
        dist_label.set('x', str(base_x))
        dist_label.set('y', str(base_y))
        for key, value in label_style.items():
            dist_label.set(key, value)
        dist_label.text = "Distance"
        
        dist_value = ET.SubElement(stats_group, '{http://www.w3.org/2000/svg}text')
        dist_value.set('x', str(base_x))
        dist_value.set('y', str(base_y + 5))
        for key, value in stats_style.items():
            dist_value.set(key, value)
        dist_value.text = f"{distance_km:.1f} km"
        
        # Temps
        time_label = ET.SubElement(stats_group, '{http://www.w3.org/2000/svg}text')
        time_label.set('x', str(base_x))
        time_label.set('y', str(base_y + 15))
        for key, value in label_style.items():
            time_label.set(key, value)
        time_label.text = "Temps"
        
        time_value = ET.SubElement(stats_group, '{http://www.w3.org/2000/svg}text')
        time_value.set('x', str(base_x))
        time_value.set('y', str(base_y + 20))
        for key, value in stats_style.items():
            time_value.set(key, value)
        time_value.text = time_str
        
        # Vitesse moyenne
        speed_label = ET.SubElement(stats_group, '{http://www.w3.org/2000/svg}text')
        speed_label.set('x', str(base_x))
        speed_label.set('y', str(base_y + 30))
        for key, value in label_style.items():
            speed_label.set(key, value)
        speed_label.text = "Vitesse moy."
        
        speed_value = ET.SubElement(stats_group, '{http://www.w3.org/2000/svg}text')
        speed_value.set('x', str(base_x))
        speed_value.set('y', str(base_y + 35))
        for key, value in stats_style.items():
            speed_value.set(key, value)
        speed_value.text = f"{avg_speed:.1f} km/h"
        
        # Dénivelé
        if elevation_gain > 0:
            elev_label = ET.SubElement(stats_group, '{http://www.w3.org/2000/svg}text')
            elev_label.set('x', str(base_x + 35))
            elev_label.set('y', str(base_y))
            for key, value in label_style.items():
                elev_label.set(key, value)
            elev_label.text = "Dénivelé +"
            
            elev_value = ET.SubElement(stats_group, '{http://www.w3.org/2000/svg}text')
            elev_value.set('x', str(base_x + 35))
            elev_value.set('y', str(base_y + 5))
            for key, value in stats_style.items():
                elev_value.set(key, value)
            elev_value.text = f"{int(elevation_gain)} m"
        
        # Ajouter le groupe à la racine SVG
        self.svg_root.append(stats_group)
    
    def generate_elevation_profile(self, coordinates: List[Tuple[float, float, float]]) -> str:
        """
        Générer le profil d'altitude comme SVG
        coordinates: list de (lat, lon, elevation)
        """
        if not coordinates or len(coordinates) < 2:
            return ""
            
        # Extraire les altitudes
        elevations = [coord[2] for coord in coordinates if len(coord) > 2 and coord[2] is not None]
        
        if not elevations:
            return ""
            
        # Créer le graphique matplotlib
        fig, ax = plt.subplots(figsize=(4, 1.5), dpi=100)
        
        # Calculer les distances cumulées (approximation)
        distances = []
        total_dist = 0
        distances.append(0)
        
        for i in range(1, len(coordinates)):
            # Distance euclidienne simple (à améliorer avec formule haversine)
            lat1, lon1 = coordinates[i-1][:2]
            lat2, lon2 = coordinates[i][:2]
            dist = ((lat2 - lat1) ** 2 + (lon2 - lon1) ** 2) ** 0.5 * 111000  # approximation en mètres
            total_dist += dist
            distances.append(total_dist / 1000)  # en km
        
        # Tracer le profil
        ax.fill_between(distances, elevations, alpha=0.6, color='#ff6b35')
        ax.plot(distances, elevations, color='#d63031', linewidth=1.5)
        
        # Style
        ax.set_xlim(0, max(distances))
        ax.set_ylim(min(elevations) - 10, max(elevations) + 10)
        ax.set_xlabel('Distance (km)', fontsize=8)
        ax.set_ylabel('Altitude (m)', fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.tick_params(labelsize=6)
        
        # Supprimer les marges
        plt.tight_layout(pad=0.1)
        
        # Convertir en SVG
        svg_buffer = io.StringIO()
        fig.savefig(svg_buffer, format='svg', bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close(fig)
        
        svg_content = svg_buffer.getvalue()
        svg_buffer.close()
        
        return svg_content
    
    def generate_elevation_widget(self, activity_data: Dict[str, Any]) -> None:
        """
        Générer le widget de profil d'altitude
        Position: widget-map (x=71.67, y=35, w=133.33, h=50)
        """
        coordinates = activity_data.get('coordinates', [])
        
        if not coordinates:
            # Widget vide si pas de coordonnées
            empty_text = ET.Element('{http://www.w3.org/2000/svg}text')
            empty_text.set('x', '138')
            empty_text.set('y', '60')
            empty_text.set('text-anchor', 'middle')
            empty_text.set('font-family', 'Arial, sans-serif')
            empty_text.set('font-size', '4mm')
            empty_text.set('fill', '#999999')
            empty_text.text = "Pas de données d'altitude"
            self.svg_root.append(empty_text)
            return
            
        # Générer le graphique SVG
        elevation_svg = self.generate_elevation_profile(coordinates)
        
        if elevation_svg:
            # Parser le SVG généré par matplotlib
            try:
                elevation_tree = ET.fromstring(elevation_svg)
                
                # Créer un groupe pour le profil d'altitude
                elevation_group = ET.Element('{http://www.w3.org/2000/svg}g')
                elevation_group.set('id', 'elevation-profile')
                elevation_group.set('transform', 'translate(74, 37) scale(0.85)')
                
                # Copier le contenu du SVG matplotlib
                for child in elevation_tree:
                    elevation_group.append(child)
                
                self.svg_root.append(elevation_group)
                
            except Exception as e:
                print(f"Erreur lors de l'intégration du profil d'altitude: {e}")
    
    def generate_map_widget(self, activity_data: Dict[str, Any]) -> None:
        """
        Générer le widget de carte GPX
        Position: widget-large (x=5, y=95, w=200, h=180)
        """
        coordinates = activity_data.get('coordinates', [])
        
        if not coordinates:
            # Widget vide si pas de coordonnées
            empty_text = ET.Element('{http://www.w3.org/2000/svg}text')
            empty_text.set('x', '105')
            empty_text.set('y', '185')
            empty_text.set('text-anchor', 'middle')
            empty_text.set('font-family', 'Arial, sans-serif')
            empty_text.set('font-size', '6mm')
            empty_text.set('fill', '#999999')
            empty_text.text = "Pas de données GPS"
            self.svg_root.append(empty_text)
            return
        
        # Extraire lat/lon
        lats = [coord[0] for coord in coordinates]
        lons = [coord[1] for coord in coordinates]
        
        # Calculer les limites
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)
        
        # Dimensions du widget
        widget_x, widget_y = 8, 98
        widget_width, widget_height = 194, 174
        
        # Normaliser les coordonnées au widget
        def normalize_coord(lat, lon):
            norm_x = ((lon - min_lon) / (max_lon - min_lon)) * widget_width + widget_x
            norm_y = ((max_lat - lat) / (max_lat - min_lat)) * widget_height + widget_y
            return norm_x, norm_y
        
        # Créer le tracé
        path_data = []
        for i, (lat, lon) in enumerate(zip(lats, lons)):
            x, y = normalize_coord(lat, lon)
            if i == 0:
                path_data.append(f"M {x:.2f} {y:.2f}")
            else:
                path_data.append(f"L {x:.2f} {y:.2f}")
        
        # Créer l'élément path
        track_path = ET.Element('{http://www.w3.org/2000/svg}path')
        track_path.set('d', ' '.join(path_data))
        track_path.set('fill', 'none')
        track_path.set('stroke', '#e17055')
        track_path.set('stroke-width', '2')
        track_path.set('stroke-linecap', 'round')
        track_path.set('stroke-linejoin', 'round')
        
        # Points de départ et d'arrivée
        start_x, start_y = normalize_coord(lats[0], lons[0])
        end_x, end_y = normalize_coord(lats[-1], lons[-1])
        
        # Point de départ (vert)
        start_circle = ET.Element('{http://www.w3.org/2000/svg}circle')
        start_circle.set('cx', str(start_x))
        start_circle.set('cy', str(start_y))
        start_circle.set('r', '3')
        start_circle.set('fill', '#00b894')
        start_circle.set('stroke', 'white')
        start_circle.set('stroke-width', '1')
        
        # Point d'arrivée (rouge)
        end_circle = ET.Element('{http://www.w3.org/2000/svg}circle')
        end_circle.set('cx', str(end_x))
        end_circle.set('cy', str(end_y))
        end_circle.set('r', '3')
        end_circle.set('fill', '#d63031')
        end_circle.set('stroke', 'white')
        end_circle.set('stroke-width', '1')
        
        # Ajouter les éléments
        self.svg_root.append(track_path)
        self.svg_root.append(start_circle)
        self.svg_root.append(end_circle)
    
    def generate_poster(self, activity_data: Dict[str, Any]) -> str:
        """
        Générer le poster complet
        """
        self.load_template()
        
        # Générer les widgets
        self.generate_stats_widget(activity_data)
        self.generate_elevation_widget(activity_data)
        self.generate_map_widget(activity_data)
        
        # Retourner le SVG final
        return ET.tostring(self.svg_root, encoding='unicode')
    
    def save_svg(self, activity_data: Dict[str, Any], output_path: str) -> str:
        """
        Sauvegarder le poster en SVG
        """
        svg_content = self.generate_poster(activity_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
            
        return output_path