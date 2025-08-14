"""
Formateurs de données pour les posters Strava
Contient les méthodes de formatage des statistiques et données d'activité
"""

from typing import Dict, Any
from datetime import datetime


class DataFormatters:
    """Formateurs de données pour l'affichage dans les posters"""
    
    @staticmethod
    def format_activity_statistics(activity_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Formate les statistiques de l'activité pour l'affichage
        
        Args:
            activity_data: Données de l'activité
            
        Returns:
            Dict avec les statistiques formatées
        """
        distance_km = activity_data.get('distance', 0) / 1000
        duration_s = activity_data.get('moving_time', 0)
        duration_formatted = DataFormatters.format_duration(duration_s)
        
        elevation_gain = activity_data.get('total_elevation_gain', 0)
        activity_type = activity_data.get('type', 'Activité')
        
        return {
            'ACTIVITY_NAME': activity_data.get('name', 'Activité Strava'),
            'DISTANCE': f"{distance_km:.1f} km",
            'DURATION': duration_formatted,
            'ELEVATION_GAIN': f"{elevation_gain:.0f} m" if elevation_gain else "-- m",
            'ACTIVITY_TYPE': activity_type
        }
    
    @staticmethod
    def format_duration(duration_seconds: int) -> str:
        """
        Formate une durée en secondes vers un format lisible
        
        Args:
            duration_seconds: Durée en secondes
            
        Returns:
            Durée formatée (ex: "1h23m", "45m", "2h00m")
        """
        if duration_seconds <= 0:
            return "0m"
        
        hours = duration_seconds // 3600
        minutes = (duration_seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}h{minutes:02d}m"
        else:
            return f"{minutes}m"
    
    @staticmethod
    def format_distance(distance_meters: float) -> str:
        """
        Formate une distance en mètres vers un format lisible
        
        Args:
            distance_meters: Distance en mètres
            
        Returns:
            Distance formatée (ex: "12.5 km", "850 m")
        """
        if distance_meters >= 1000:
            return f"{distance_meters / 1000:.1f} km"
        else:
            return f"{distance_meters:.0f} m"
    
    @staticmethod
    def format_elevation(elevation_meters: float) -> str:
        """
        Formate un dénivelé en mètres
        
        Args:
            elevation_meters: Dénivelé en mètres
            
        Returns:
            Dénivelé formaté (ex: "850 m", "-- m")
        """
        if elevation_meters > 0:
            return f"{elevation_meters:.0f} m"
        else:
            return "-- m"
    
    @staticmethod
    def format_pace(pace_min_per_km: float) -> str:
        """
        Formate une allure en minutes par kilomètre
        
        Args:
            pace_min_per_km: Allure en minutes décimales par kilomètre
            
        Returns:
            Allure formatée (ex: "5:24", "4:12")
        """
        if pace_min_per_km <= 0:
            return "--:--"
        
        minutes = int(pace_min_per_km)
        seconds = int((pace_min_per_km - minutes) * 60)
        return f"{minutes}:{seconds:02d}"
    
    @staticmethod
    def format_speed(speed_kmh: float) -> str:
        """
        Formate une vitesse en km/h
        
        Args:
            speed_kmh: Vitesse en km/h
            
        Returns:
            Vitesse formatée (ex: "12.5 km/h")
        """
        if speed_kmh <= 0:
            return "-- km/h"
        
        return f"{speed_kmh:.1f} km/h"
    
    @staticmethod
    def format_date(date_str: str) -> str:
        """
        Formate une date pour l'affichage
        
        Args:
            date_str: Date au format ISO (ex: "2024-01-15T14:30:00Z")
            
        Returns:
            Date formatée (ex: "15 Jan 2024")
        """
        try:
            # Parser la date ISO
            if 'T' in date_str:
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                date_obj = datetime.fromisoformat(date_str)
            
            # Format français
            months = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun',
                     'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
            
            return f"{date_obj.day} {months[date_obj.month-1]} {date_obj.year}"
            
        except Exception:
            return date_str  # Retourner la chaîne originale en cas d'erreur
    
    @staticmethod
    def format_activity_type_french(activity_type: str) -> str:
        """
        Traduit les types d'activité Strava en français
        
        Args:
            activity_type: Type d'activité Strava (ex: "Run", "Ride")
            
        Returns:
            Type d'activité en français
        """
        translations = {
            'Run': 'Course',
            'Ride': 'Vélo',
            'Walk': 'Marche',
            'Hike': 'Randonnée',
            'Swim': 'Natation',
            'WeightTraining': 'Musculation',
            'Workout': 'Entraînement',
            'Yoga': 'Yoga',
            'VirtualRun': 'Course virtuelle',
            'VirtualRide': 'Vélo virtuel',
            'TrailRun': 'Trail',
            'MountainBikeRide': 'VTT',
            'RoadBikeRide': 'Vélo de route',
        }
        
        return translations.get(activity_type, activity_type)
    
    @staticmethod
    def create_poster_replacements(activity_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Crée le dictionnaire complet des remplacements pour le template
        Combine le formatage des statistiques avec d'autres données
        
        Args:
            activity_data: Données de l'activité
            
        Returns:
            Dict complet des remplacements pour le template SVG
        """
        # Statistiques de base formatées
        stats = DataFormatters.format_activity_statistics(activity_data)
        
        # Ajouter d'autres données formatées si disponibles
        replacements = {
            'ACTIVITY_NAME': stats['ACTIVITY_NAME'],
            'DISTANCE': stats['DISTANCE'],
            'DURATION': stats['DURATION'],
            'ELEVATION_GAIN': stats['ELEVATION_GAIN'],
            'ACTIVITY_TYPE': DataFormatters.format_activity_type_french(stats['ACTIVITY_TYPE'])
        }
        
        # Ajouter la date si disponible
        if 'start_date' in activity_data:
            replacements['ACTIVITY_DATE'] = DataFormatters.format_date(activity_data['start_date'])
        
        # Ajouter la vitesse moyenne si calculable
        if activity_data.get('distance', 0) > 0 and activity_data.get('moving_time', 0) > 0:
            speed_ms = activity_data['distance'] / activity_data['moving_time']
            speed_kmh = speed_ms * 3.6
            replacements['AVERAGE_SPEED'] = DataFormatters.format_speed(speed_kmh)
            replacements['AVERAGE_PACE'] = DataFormatters.format_pace(60 / speed_kmh)
        
        return replacements