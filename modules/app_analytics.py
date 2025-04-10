from flask import Flask, request, redirect, jsonify, Blueprint
from pymongo import MongoClient
from datetime import datetime
from user_agents import parse
import json
import requests
from collections import Counter
import os
from dotenv import load_dotenv

load_dotenv()


# MongoDB connection
client = MongoClient(os.getenv('MONGODB_URI'))
db = client['shortly']
collection = db['urls']

class AnalyticsModule:
    def __init__(self):
        self.bp = Blueprint('analytics', __name__, url_prefix='')
        self.register_routes()
    def register_routes(self):
        @self.bp.route('/<short>')
        def get_info_and_redirect(short):
            #location from ip address
            def get_location(ip):
                url = f"http://ip-api.com/json/{ip}"
                try:
                    response = requests.get(url, timeout=5)  # Add a timeout
                    response.raise_for_status()  # Raise an exception for HTTP errors
                    data = response.json()
                    return {
                        "country": data.get("country", "Unknown"),
                        "region": data.get("regionName", "Unknown"),
                        "city": data.get("city", "Unknown")
                    }
                except requests.exceptions.RequestException as e:
                    return {
                        "country": "Unknown",
                        "region": "Unknown",
                        "city": "Unknown"
                    }
            url=collection.find_one({'shortCode':short})
            if not url:
                return "URL not found",404
    
            #Getting the data of a click
            now=datetime.utcnow()
            user_agent=parse(request.user_agent.string)
            if request.headers.get('X-Forwarded-For'):
                ip_address = request.headers.get('X-Forwarded-For').split(',')[0]#first ip in the list
            else:
                ip_address = request.remote_addr
    
            location_data = get_location(ip_address)
            click_data = {
                "time": now.strftime("%H:%M:%S"),
                "date": now.day,
                "month": now.strftime("%B"),
                "year": now.year,
                "day": now.strftime("%A"),
                "device": user_agent.device.family,
                "os": user_agent.os.family,
                "browser": user_agent.browser.family,
                "ip": ip_address,
                "country": location_data["country"],                    
                "region": location_data["region"],
                "city": location_data["city"]
            }
            #Getting unique visitors
            collection.update_one(
                {"shortCode": short, "click_data.ip": {"$ne": ip_address}},  #Checking if IP does not already exist
                {"$inc": {"unique_visitors": 1}}, 
                upsert=True
                )

            #Updating MongoDB
            collection.update_one(
                {"shortCode": short},
                {"$push": {"click_data": click_data}}
            )

            collection.update_one(
                {"shortCode": short},
                {"$inc": {"clicks": 1}}
            )
    
            return redirect(url['longUrl'])
        #Getting impressions for ctr
        @self.bp.route('/impression/<short>')
        def count_impression(short):
            collection.update_one(
                {"shortCode": short},
                {"$inc": {"impressions": 1}}, 
                upsert=True 
            )
            return "Impression counted", 200
        #Displaying ctr
        @self.bp.route('/ctr/<short>')
        def getctr(short):
            url=collection.find_one({'shortCode':short})
            if not url:
                return "short code not found"
            if "click_data" not in url:
                return "No clicks yet"
            if "impressions" not in url:
                return "No impressions yet"
            clicks=len(url.get('click_data'))
            impressions=url.get('impressions')
            ctr=round(clicks/impressions,2)
            display={"shortCode": short, "ctr": ctr, "totalImpressions": impressions, "clicks": clicks}
            return jsonify(display)
        
        #Displaying analytics
        @self.bp.route('/analytics/<short>')
        def get_analytics(short):
            url=collection.find_one({'shortCode':short})
            if not url:
                return "Short code does not exist", 404
            clicks=url['clicks']
    
            device = Counter(click['device'] for click in url['click_data'])
            os = Counter(click['os'] for click in url['click_data'])
            browser = Counter(click['browser'] for click in url['click_data'])

            display={"shortCode": short, "totalClicks": clicks, "uniqueVisitors": url.get('unique_visitors',0), "deviceDistribution": device, "osDistribution": os, "browserDistribution": browser}
            return jsonify(display)
        
    def get_blueprint(self):
        return self.bp

