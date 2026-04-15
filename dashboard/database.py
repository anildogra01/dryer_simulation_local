"""
Database configuration and models for Grain Dryer Simulation
SQLite database for local development
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    """User accounts for authentication and personal history"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    simulations = db.relationship('Simulation', backref='user', lazy=True)
    comments = db.relationship('Comment', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'


class Crop(db.Model):
    """Store crop/grain types and their properties"""
    __tablename__ = 'crops'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(200))
    initial_moisture = db.Column(db.Float)  # Default initial moisture %
    target_moisture = db.Column(db.Float)   # Target moisture %
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'initial_moisture': self.initial_moisture,
            'target_moisture': self.target_moisture,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Crop {self.name}>'


class Simulation(db.Model):
    """Store simulation runs"""
    __tablename__ = 'simulations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Link to user
    crop_id = db.Column(db.Integer, db.ForeignKey('crops.id'))
    
    # Model and method
    model_type = db.Column(db.String(50))  # thompson, page, henderson_pabis, exponential
    processing_method = db.Column(db.String(20))  # regular, rk4
    
    # Input parameters
    initial_moisture = db.Column(db.Float, nullable=False)
    target_moisture = db.Column(db.Float, nullable=False)
    grain_temp = db.Column(db.Float)
    air_temp = db.Column(db.Float)
    air_rh = db.Column(db.Float)
    air_flow_rate = db.Column(db.Float)
    grain_flow_rate = db.Column(db.Float)
    width = db.Column(db.Float)
    length = db.Column(db.Float)
    
    # Dryer dimensions
    dryer_width = db.Column(db.Float)  # ft
    dryer_length = db.Column(db.Float)  # ft
    bed_depth = db.Column(db.Float)  # ft
    
    # Simulation results
    status = db.Column(db.String(20), default='pending')  # pending, running, complete, stopped, error
    total_time = db.Column(db.Float)  # hours
    total_energy = db.Column(db.Float)  # BTU
    total_water_removed = db.Column(db.Float)  # lb
    final_moisture = db.Column(db.Float)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationship
    crop = db.relationship('Crop', backref='simulations')
    
    def to_dict(self):
        return {
            'id': self.id,
            'crop_id': self.crop_id,
            'crop_name': self.crop.name if self.crop else None,
            'model_type': self.model_type,
            'processing_method': self.processing_method,
            'initial_moisture': self.initial_moisture,
            'target_moisture': self.target_moisture,
            'grain_temp': self.grain_temp,
            'air_temp': self.air_temp,
            'air_rh': self.air_rh,
            'air_flow_rate': self.air_flow_rate,
            'grain_flow_rate': self.grain_flow_rate,
            'width': self.width,
            'length': self.length,
            'dryer_width': self.dryer_width,
            'dryer_length': self.dryer_length,
            'bed_depth': self.bed_depth,
            'status': self.status,
            'total_time': self.total_time,
            'total_energy': self.total_energy,
            'total_water_removed': self.total_water_removed,
            'final_moisture': self.final_moisture,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    def __repr__(self):
        return f'<Simulation {self.id} - {self.status}>'


class IterationData(db.Model):
    """Store iteration-by-iteration simulation data"""
    __tablename__ = 'iteration_data'
    
    id = db.Column(db.Integer, primary_key=True)
    simulation_id = db.Column(db.Integer, db.ForeignKey('simulations.id'), nullable=False)
    iteration = db.Column(db.Integer, nullable=False)
    time = db.Column(db.Float, nullable=False)  # hours
    moisture = db.Column(db.Float, nullable=False)  # % - average moisture
    drying_rate = db.Column(db.Float)  # %/hr - rate of moisture change
    energy = db.Column(db.Float, nullable=False)  # BTU
    water_removed = db.Column(db.Float, nullable=False)  # lb
    grain_temp = db.Column(db.Float)  # °F
    air_temp = db.Column(db.Float)  # °F
    
    # Gradient data - moisture at different bed layers (JSON format)
    # Stores array of moisture values from bottom (air inlet) to top
    moisture_gradient = db.Column(db.Text)  # JSON array: [bottom, layer2, layer3, ..., top]
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    simulation = db.relationship('Simulation', backref='iterations')
    
    def to_dict(self):
        return {
            'id': self.id,
            'simulation_id': self.simulation_id,
            'iteration': self.iteration,
            'time': self.time,
            'moisture': self.moisture,
            'drying_rate': self.drying_rate,
            'energy': self.energy,
            'water_removed': self.water_removed,
            'grain_temp': self.grain_temp,
            'air_temp': self.air_temp,
            'moisture_gradient': json.loads(self.moisture_gradient) if self.moisture_gradient else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<IterationData Sim:{self.simulation_id} Iter:{self.iteration}>'


class Comment(db.Model):
    """Store user comments and reviews for simulations"""
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    simulation_id = db.Column(db.Integer, db.ForeignKey('simulations.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Link to user
    author = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer)  # 1-5 stars
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    simulation = db.relationship('Simulation', backref='comments')
    
    def to_dict(self):
        return {
            'id': self.id,
            'simulation_id': self.simulation_id,
            'author': self.author,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Comment {self.id} by {self.author}>'


class DashboardSettings(db.Model):
    """Store dashboard/page customization settings"""
    __tablename__ = 'dashboard_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    page_name = db.Column(db.String(50), nullable=False)  # home, simulation, crop, history, reports
    
    # Title and Content
    title = db.Column(db.String(200))
    subtitle = db.Column(db.String(200))
    description = db.Column(db.Text)
    
    # Title Styling
    title_font = db.Column(db.String(100))
    title_size = db.Column(db.String(20))  # e.g., "24px", "2rem"
    title_color = db.Column(db.String(20))  # hex color
    title_bg_color = db.Column(db.String(20))
    
    # Subtitle Styling
    subtitle_font = db.Column(db.String(100))
    subtitle_size = db.Column(db.String(20))
    subtitle_color = db.Column(db.String(20))
    
    # Description Styling
    description_font = db.Column(db.String(100))
    description_size = db.Column(db.String(20))
    description_color = db.Column(db.String(20))
    
    # Background
    page_bg_color = db.Column(db.String(20))
    content_bg_color = db.Column(db.String(20))
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'page_name': self.page_name,
            'title': self.title,
            'subtitle': self.subtitle,
            'description': self.description,
            'title_font': self.title_font,
            'title_size': self.title_size,
            'title_color': self.title_color,
            'title_bg_color': self.title_bg_color,
            'subtitle_font': self.subtitle_font,
            'subtitle_size': self.subtitle_size,
            'subtitle_color': self.subtitle_color,
            'description_font': self.description_font,
            'description_size': self.description_size,
            'description_color': self.description_color,
            'page_bg_color': self.page_bg_color,
            'content_bg_color': self.content_bg_color,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<DashboardSettings {self.page_name}>'


class Location(db.Model):
    """Physical locations where grain bins are installed"""
    __tablename__ = 'locations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    name = db.Column(db.String(100), nullable=False)  # e.g., "Farm A", "Main Silo"
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(50))
    country = db.Column(db.String(50))
    zip_code = db.Column(db.String(20))
    
    # GPS coordinates for map display
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    # Contact info
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='locations')
    bins = db.relationship('Bin', backref='location', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'zip_code': self.zip_code,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'contact_person': self.contact_person,
            'phone': self.phone,
            'email': self.email,
            'is_active': self.is_active,
            'notes': self.notes,
            'bin_count': len(self.bins),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Location {self.name}>'


class Bin(db.Model):
    """Individual grain storage bins with ESP32 sensors"""
    __tablename__ = 'bins'
    
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    
    # Bin identification
    name = db.Column(db.String(100), nullable=False)  # e.g., "Bin 1A", "South Bin"
    bin_number = db.Column(db.String(50))  # Physical bin number/label
    
    # ESP32 device info
    device_id = db.Column(db.String(100), unique=True)  # ESP32 MAC address or unique ID
    device_api_key = db.Column(db.String(100))  # Authentication key for ESP32
    
    # Physical characteristics
    capacity_bushels = db.Column(db.Float)  # Storage capacity
    diameter_ft = db.Column(db.Float)
    height_ft = db.Column(db.Float)
    bin_type = db.Column(db.String(50))  # flat, hopper, etc.
    
    # Current status
    is_online = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime)  # Last data received from ESP32
    current_crop_id = db.Column(db.Integer, db.ForeignKey('crops.id'))
    
    # Sensor configuration
    has_sht31 = db.Column(db.Boolean, default=True)
    has_dht11 = db.Column(db.Boolean, default=True)
    has_moisture_sensor = db.Column(db.Boolean, default=False)
    has_airflow_sensor = db.Column(db.Boolean, default=False)
    
    # Alert thresholds
    alert_high_temp = db.Column(db.Float, default=80.0)  # °F
    alert_high_humidity = db.Column(db.Float, default=70.0)  # %
    alert_target_moisture = db.Column(db.Float, default=15.0)  # %
    
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    current_crop = db.relationship('Crop', foreign_keys=[current_crop_id])
    sensor_readings = db.relationship('SensorReading', backref='bin', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'location_id': self.location_id,
            'name': self.name,
            'bin_number': self.bin_number,
            'device_id': self.device_id,
            'capacity_bushels': self.capacity_bushels,
            'diameter_ft': self.diameter_ft,
            'height_ft': self.height_ft,
            'bin_type': self.bin_type,
            'is_online': self.is_online,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'current_crop': self.current_crop.to_dict() if self.current_crop else None,
            'has_sht31': self.has_sht31,
            'has_dht11': self.has_dht11,
            'has_moisture_sensor': self.has_moisture_sensor,
            'has_airflow_sensor': self.has_airflow_sensor,
            'alert_high_temp': self.alert_high_temp,
            'alert_high_humidity': self.alert_high_humidity,
            'alert_target_moisture': self.alert_target_moisture,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Bin {self.name}>'


class SensorReading(db.Model):
    """Time-series sensor data from ESP32 devices"""
    __tablename__ = 'sensor_readings'
    
    id = db.Column(db.Integer, primary_key=True)
    bin_id = db.Column(db.Integer, db.ForeignKey('bins.id'), nullable=False, index=True)
    
    # Timestamp
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Temperature readings
    temp_sht31 = db.Column(db.Float)  # °F from SHT31
    temp_dht11 = db.Column(db.Float)  # °F from DHT11
    temp_avg = db.Column(db.Float)  # Average temperature
    
    # Humidity readings
    humidity_sht31 = db.Column(db.Float)  # % from SHT31
    humidity_dht11 = db.Column(db.Float)  # % from DHT11
    humidity_avg = db.Column(db.Float)  # Average humidity
    
    # Additional sensors (future)
    grain_moisture = db.Column(db.Float)  # % moisture content
    airflow_cfm = db.Column(db.Float)  # Air flow rate
    co2_ppm = db.Column(db.Float)  # CO2 level
    
    # Calculated/derived values
    dew_point = db.Column(db.Float)  # Calculated dew point
    heat_index = db.Column(db.Float)  # Heat index
    
    # Device health
    esp32_uptime_sec = db.Column(db.Integer)  # ESP32 uptime in seconds
    wifi_rssi = db.Column(db.Integer)  # WiFi signal strength
    battery_voltage = db.Column(db.Float)  # If battery powered
    
    def to_dict(self):
        return {
            'id': self.id,
            'bin_id': self.bin_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'temp_sht31': self.temp_sht31,
            'temp_dht11': self.temp_dht11,
            'temp_avg': self.temp_avg,
            'humidity_sht31': self.humidity_sht31,
            'humidity_dht11': self.humidity_dht11,
            'humidity_avg': self.humidity_avg,
            'grain_moisture': self.grain_moisture,
            'airflow_cfm': self.airflow_cfm,
            'co2_ppm': self.co2_ppm,
            'dew_point': self.dew_point,
            'heat_index': self.heat_index,
            'esp32_uptime_sec': self.esp32_uptime_sec,
            'wifi_rssi': self.wifi_rssi,
            'battery_voltage': self.battery_voltage
        }
    
    def __repr__(self):
        return f'<SensorReading Bin:{self.bin_id} at {self.timestamp}>'


class PasswordReset(db.Model):
    """Store password reset codes"""
    __tablename__ = 'password_resets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    reset_code = db.Column(db.String(10), nullable=False)  # 6-digit code
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)  # Valid for 1 hour
    
    # Relationship
    user = db.relationship('User', backref='password_resets')
    
    def is_valid(self):
        """Check if reset code is still valid"""
        return not self.is_used and datetime.utcnow() < self.expires_at
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'is_used': self.is_used,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
    
    def __repr__(self):
        return f'<PasswordReset {self.email}>'


def init_db(app):
    """Initialize database with app context"""
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create default admin user if doesn't exist
        if User.query.count() == 0:
            admin = User(
                username='admin',
                email='admin@graindrying.com',
                full_name='System Administrator',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Default admin user created:")
            print("   Username: admin")
            print("   Password: admin123")
            print("   ⚠️  CHANGE THIS PASSWORD AFTER FIRST LOGIN!")
        
        # Check if we need to seed initial data
        if Crop.query.count() == 0:
            seed_initial_data()


def seed_initial_data():
    """Seed database with initial crop data"""
    
    # Add common grain crops
    crops = [
        Crop(name='Corn', description='Yellow Dent Corn', initial_moisture=25.0, target_moisture=15.0),
        Crop(name='Wheat', description='Hard Red Winter Wheat', initial_moisture=20.0, target_moisture=13.5),
        Crop(name='Soybeans', description='Yellow Soybeans', initial_moisture=18.0, target_moisture=13.0),
        Crop(name='Rice', description='Long Grain Rice', initial_moisture=22.0, target_moisture=12.0),
        Crop(name='Barley', description='Two-Row Barley', initial_moisture=20.0, target_moisture=12.0),
    ]
    db.session.add_all(crops)
    db.session.commit()
    
    print("✅ Database seeded with initial crop data")
