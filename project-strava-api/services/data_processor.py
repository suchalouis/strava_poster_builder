"""
Module de traitement et d'analyse des données Strava
Calcule des statistiques, génère des résumés et prépare les données pour la visualisation
"""

from typing import Dict, List
from datetime import datetime, timedelta
from collections import defaultdict


class StravaDataProcessor:
    """Processeur pour analyser et traiter les données Strava"""
    
    def __init__(self):
        pass
    
    @staticmethod
    def format_distance(meters: float) -> str:
        """Formater la distance en kilomètres"""
        km = meters / 1000
        return f"{km:.1f} km"
    
    @staticmethod
    def format_time(seconds: int) -> str:
        """Formater le temps en heures et minutes"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}h{minutes:02d}"
        else:
            return f"{minutes}min"
    
    @staticmethod
    def format_elevation(meters: float) -> str:
        """Formater l'élévation"""
        return f"{int(meters)}m"
    
    @staticmethod
    def format_pace(distance_m: float, time_s: int) -> str:
        """Calculer et formater l'allure (min/km)"""
        if distance_m == 0:
            return "0:00"
        
        pace_s_per_km = (time_s * 1000) / distance_m
        minutes = int(pace_s_per_km // 60)
        seconds = int(pace_s_per_km % 60)
        return f"{minutes}:{seconds:02d}"
    
    @staticmethod
    def get_activity_icon(activity_type: str) -> str:
        """Obtenir l'icône pour un type d'activité"""
        icons = {
            'Run': '🏃‍♂️',
            'Ride': '🚴‍♂️', 
            'Swim': '🏊‍♂️',
            'Hike': '🥾',
            'Walk': '🚶‍♂️',
            'WeightTraining': '🏋️‍♂️',
            'Workout': '💪',
            'Yoga': '🧘‍♂️'
        }
        return icons.get(activity_type, '🏃‍♂️')
    
    def process_athlete_stats(self, stats_data: Dict) -> Dict:
        """Traiter les statistiques d'un athlète"""
        all_ride = stats_data.get('all_ride_totals', {})
        all_run = stats_data.get('all_run_totals', {})
        all_swim = stats_data.get('all_swim_totals', {})
        
        return {
            'total_activities': (
                all_ride.get('count', 0) + 
                all_run.get('count', 0) + 
                all_swim.get('count', 0)
            ),
            'total_distance': self.format_distance(
                all_ride.get('distance', 0) + 
                all_run.get('distance', 0) + 
                all_swim.get('distance', 0)
            ),
            'total_time': self.format_time(
                all_ride.get('moving_time', 0) + 
                all_run.get('moving_time', 0) + 
                all_swim.get('moving_time', 0)
            ),
            'total_elevation': self.format_elevation(
                all_ride.get('elevation_gain', 0) + 
                all_run.get('elevation_gain', 0) + 
                all_swim.get('elevation_gain', 0)
            ),
            'by_sport': {
                'running': {
                    'activities': all_run.get('count', 0),
                    'distance': self.format_distance(all_run.get('distance', 0)),
                    'time': self.format_time(all_run.get('moving_time', 0)),
                    'elevation': self.format_elevation(all_run.get('elevation_gain', 0))
                },
                'cycling': {
                    'activities': all_ride.get('count', 0),
                    'distance': self.format_distance(all_ride.get('distance', 0)),
                    'time': self.format_time(all_ride.get('moving_time', 0)),
                    'elevation': self.format_elevation(all_ride.get('elevation_gain', 0))
                },
                'swimming': {
                    'activities': all_swim.get('count', 0),
                    'distance': self.format_distance(all_swim.get('distance', 0)),
                    'time': self.format_time(all_swim.get('moving_time', 0))
                }
            }
        }
    
    def process_activities_summary(self, activities: List[Dict]) -> Dict:
        """Créer un résumé des activités"""
        if not activities:
            return {
                'total_activities': 0,
                'total_distance': '0.0 km',
                'total_time': '0h00',
                'total_elevation': '0m',
                'by_type': {},
                'recent_activities': []
            }
        
        total_distance = 0
        total_time = 0
        total_elevation = 0
        by_type = defaultdict(lambda: {
            'count': 0, 
            'distance': 0, 
            'time': 0, 
            'elevation': 0
        })
        
        # Traiter chaque activité
        for activity in activities:
            distance = activity.get('distance', 0)
            time = activity.get('moving_time', 0)
            elevation = activity.get('total_elevation_gain', 0)
            activity_type = activity.get('type', 'Unknown')
            
            total_distance += distance
            total_time += time
            total_elevation += elevation
            
            by_type[activity_type]['count'] += 1
            by_type[activity_type]['distance'] += distance
            by_type[activity_type]['time'] += time
            by_type[activity_type]['elevation'] += elevation
        
        # Formater les données par type
        formatted_by_type = {}
        for activity_type, data in by_type.items():
            formatted_by_type[activity_type] = {
                'count': data['count'],
                'distance': self.format_distance(data['distance']),
                'time': self.format_time(data['time']),
                'elevation': self.format_elevation(data['elevation']),
                'icon': self.get_activity_icon(activity_type)
            }
        
        # Activités récentes formatées
        recent_activities = []
        for activity in activities[:10]:  # Les 10 plus récentes
            recent_activities.append({
                'id': activity.get('id'),
                'name': activity.get('name'),
                'type': activity.get('type'),
                'icon': self.get_activity_icon(activity.get('type', '')),
                'distance': self.format_distance(activity.get('distance', 0)),
                'time': self.format_time(activity.get('moving_time', 0)),
                'pace': self.format_pace(
                    activity.get('distance', 0), 
                    activity.get('moving_time', 0)
                ) if activity.get('type') == 'Run' else None,
                'elevation': self.format_elevation(activity.get('total_elevation_gain', 0)),
                'date': activity.get('start_date_local'),
                'formatted_date': self.format_date(activity.get('start_date_local'))
            })
        
        return {
            'total_activities': len(activities),
            'total_distance': self.format_distance(total_distance),
            'total_time': self.format_time(total_time),
            'total_elevation': self.format_elevation(total_elevation),
            'by_type': formatted_by_type,
            'recent_activities': recent_activities
        }
    
    @staticmethod
    def format_date(date_string: str) -> str:
        """Formater une date au format français"""
        if not date_string:
            return ""
        
        try:
            date = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return date.strftime("%d %b %Y")
        except:
            return date_string
    
    def get_monthly_stats(self, activities: List[Dict], year: int = None) -> Dict:
        """Calculer les statistiques mensuelles"""
        if year is None:
            year = datetime.now().year
            
        monthly_data = defaultdict(lambda: {
            'count': 0,
            'distance': 0,
            'time': 0,
            'elevation': 0
        })
        
        for activity in activities:
            try:
                date = datetime.fromisoformat(
                    activity.get('start_date_local', '').replace('Z', '+00:00')
                )
                if date.year == year:
                    month = date.month
                    monthly_data[month]['count'] += 1
                    monthly_data[month]['distance'] += activity.get('distance', 0)
                    monthly_data[month]['time'] += activity.get('moving_time', 0)
                    monthly_data[month]['elevation'] += activity.get('total_elevation_gain', 0)
            except:
                continue
        
        # Formater les données pour tous les mois
        formatted_monthly = {}
        month_names = [
            'Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin',
            'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc'
        ]
        
        for month in range(1, 13):
            data = monthly_data[month]
            formatted_monthly[month_names[month-1]] = {
                'count': data['count'],
                'distance': self.format_distance(data['distance']),
                'time': self.format_time(data['time']),
                'elevation': self.format_elevation(data['elevation'])
            }
        
        return formatted_monthly
    
    def get_weekly_stats(self, activities: List[Dict], weeks_back: int = 12) -> Dict:
        """Calculer les statistiques hebdomadaires"""
        now = datetime.now()
        weekly_data = []
        
        for i in range(weeks_back):
            week_start = now - timedelta(weeks=i+1)
            week_end = now - timedelta(weeks=i)
            
            week_activities = []
            for activity in activities:
                try:
                    date = datetime.fromisoformat(
                        activity.get('start_date_local', '').replace('Z', '+00:00')
                    )
                    if week_start <= date < week_end:
                        week_activities.append(activity)
                except:
                    continue
            
            week_summary = self.process_activities_summary(week_activities)
            weekly_data.append({
                'week_start': week_start.strftime("%d %b"),
                'week_end': week_end.strftime("%d %b"),
                **week_summary
            })
        
        return {
            'weekly_data': weekly_data[::-1]  # Plus récent en premier
        }
    
    def get_personal_records(self, activities: List[Dict]) -> Dict:
        """Calculer les records personnels"""
        records = {
            'longest_run': None,
            'longest_ride': None,
            'fastest_5k': None,
            'fastest_10k': None,
            'biggest_elevation': None
        }
        
        for activity in activities:
            distance = activity.get('distance', 0)
            time = activity.get('moving_time', 0)
            elevation = activity.get('total_elevation_gain', 0)
            activity_type = activity.get('type')
            
            # Plus longue course
            if (activity_type == 'Run' and 
                (records['longest_run'] is None or distance > records['longest_run']['distance'])):
                records['longest_run'] = {
                    'distance': distance,
                    'formatted_distance': self.format_distance(distance),
                    'name': activity.get('name'),
                    'date': self.format_date(activity.get('start_date_local'))
                }
            
            # Plus long vélo
            if (activity_type == 'Ride' and 
                (records['longest_ride'] is None or distance > records['longest_ride']['distance'])):
                records['longest_ride'] = {
                    'distance': distance,
                    'formatted_distance': self.format_distance(distance),
                    'name': activity.get('name'),
                    'date': self.format_date(activity.get('start_date_local'))
                }
            
            # 5K le plus rapide
            if (activity_type == 'Run' and 4800 <= distance <= 5200 and time > 0):
                if (records['fastest_5k'] is None or time < records['fastest_5k']['time']):
                    records['fastest_5k'] = {
                        'time': time,
                        'formatted_time': self.format_time(time),
                        'pace': self.format_pace(distance, time),
                        'name': activity.get('name'),
                        'date': self.format_date(activity.get('start_date_local'))
                    }
            
            # 10K le plus rapide
            if (activity_type == 'Run' and 9800 <= distance <= 10200 and time > 0):
                if (records['fastest_10k'] is None or time < records['fastest_10k']['time']):
                    records['fastest_10k'] = {
                        'time': time,
                        'formatted_time': self.format_time(time),
                        'pace': self.format_pace(distance, time),
                        'name': activity.get('name'),
                        'date': self.format_date(activity.get('start_date_local'))
                    }
            
            # Plus gros dénivelé
            if (elevation > 0 and 
                (records['biggest_elevation'] is None or elevation > records['biggest_elevation']['elevation'])):
                records['biggest_elevation'] = {
                    'elevation': elevation,
                    'formatted_elevation': self.format_elevation(elevation),
                    'name': activity.get('name'),
                    'date': self.format_date(activity.get('start_date_local'))
                }
        
        return records