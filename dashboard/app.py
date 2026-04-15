from flask import Flask, render_template, jsonify, request, redirect, url_for, session, make_response
from flask_cors import CORS
from datetime import datetime, timedelta
import math
import json
import random
import string
from database import db, init_db, Crop, Simulation, IterationData, Comment, DashboardSettings, User, PasswordReset

app = Flask(__name__)
CORS(app)

# Secret key for session management
app.secret_key = 'grain-dryer-secret-key-change-in-production'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///grain_dryer.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'grain-dryer-simulation-key'

# Initialize database
init_db(app)


@app.route('/')
def index():
    """Serve the main navigation/home page"""
    response = make_response(render_template('index.html'))
    # Prevent caching to ensure login check always runs
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route('/simulation')
def simulation():
    """Serve the simulation dashboard"""
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    response = make_response(render_template('dashboard.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route('/api/crops', methods=['GET'])
def get_crops():
    """Get all available crops"""
    crops = Crop.query.all()
    return jsonify([crop.to_dict() for crop in crops])


@app.route('/api/test', methods=['GET'])
def test_endpoint():
    """Simple test endpoint to verify API is working"""
    return jsonify({
        'status': 'OK',
        'message': 'API is working',
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/crops', methods=['POST'])
def create_crop():
    """Create a new crop"""
    data = request.json
    crop = Crop(
        name=data.get('name'),
        description=data.get('description', ''),
        initial_moisture=data.get('initial_moisture'),
        target_moisture=data.get('target_moisture')
    )
    db.session.add(crop)
    db.session.commit()
    return jsonify({'success': True, 'crop': crop.to_dict()})


@app.route('/api/simulate', methods=['POST'])
def run_simulation():
    """
    Run grain dryer simulation with input validation
    """
    try:
        data = request.json
        
        # Extract parameters with safe defaults
        crop_id = data.get('crop_id')
        model_type = data.get('model_type', 'exponential')
        processing_method = data.get('processing_method', 'regular')
        
        try:
            initial_moisture = float(data.get('initial_moisture', 25.0))
            target_moisture = float(data.get('target_moisture', 15.0))
            grain_temp = float(data.get('grain_temp', 70.0))
            air_temp = float(data.get('air_temp', 110.0))
            air_rh = float(data.get('air_rh', 30.0))
            air_flow_rate = float(data.get('air_flow_rate', 500.0))
        except (ValueError, TypeError) as e:
            return jsonify({
                'success': False,
                'error': 'Invalid number format in input fields',
                'validation_errors': ['Please check that all numeric fields contain valid numbers']
            }), 400
        
        grain_flow_rate = data.get('grain_flow_rate')
        width = data.get('width')
        length = float(data.get('length', 5.0)) if data.get('length') else 5.0
        
        # Dryer dimensions
        try:
            dryer_width = float(data.get('dryer_width', 10.0))
            dryer_length = float(data.get('dryer_length', 20.0))
            bed_depth = float(data.get('bed_depth', 2.0))
        except (ValueError, TypeError):
            dryer_width = 10.0
            dryer_length = 20.0
            bed_depth = 2.0
        
        # Backend validation
        validation_errors = []
        
        # Moisture validation
        if initial_moisture <= target_moisture:
            validation_errors.append(f'Initial moisture ({initial_moisture}%) must be higher than target moisture ({target_moisture}%)')
        if initial_moisture < 0 or initial_moisture > 100:
            validation_errors.append(f'Initial moisture must be between 0% and 100%')
        if target_moisture < 0 or target_moisture > 100:
            validation_errors.append(f'Target moisture must be between 0% and 100%')
        
        # Temperature validation
        if air_temp <= grain_temp:
            validation_errors.append(f'Air temperature ({air_temp}°F) must be higher than grain temperature ({grain_temp}°F)')
        if air_temp < 60 or air_temp > 250:
            validation_errors.append(f'Air temperature should be between 60°F and 250°F')
        if grain_temp < 32 or grain_temp > 150:
            validation_errors.append(f'Grain temperature should be between 32°F and 150°F')
        
        # Humidity validation
        if air_rh < 0 or air_rh > 100:
            validation_errors.append(f'Relative humidity must be between 0% and 100%')
        
        # Air flow validation
        if air_flow_rate <= 0:
            validation_errors.append(f'Air flow rate must be greater than 0 CFM')
        
        # Dryer dimensions validation
        if dryer_width <= 0 or dryer_length <= 0 or bed_depth <= 0:
            validation_errors.append(f'All dryer dimensions must be greater than 0')
        if bed_depth > 10:
            validation_errors.append(f'Bed depth too large ({bed_depth} ft). Maximum recommended: 10 ft')
        
        # Air flow vs capacity validation
        dryer_volume = dryer_width * dryer_length * bed_depth
        bushels = dryer_volume * 2
        cfm_per_bushel = air_flow_rate / bushels if bushels > 0 else 0
        
        if cfm_per_bushel < 0.5:
            validation_errors.append(f'Air flow too low ({cfm_per_bushel:.2f} CFM/bushel). Minimum 1 CFM/bushel recommended')
        
        # Return validation errors if any
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Input validation failed',
                'validation_errors': validation_errors
            }), 400
        
        # Create simulation record
        simulation = Simulation(
            user_id=session.get('user_id'),  # Link to logged-in user
            crop_id=crop_id,
            model_type=model_type,
            processing_method=processing_method,
            initial_moisture=initial_moisture,
            target_moisture=target_moisture,
            grain_temp=grain_temp,
            air_temp=air_temp,
            air_rh=air_rh,
            air_flow_rate=air_flow_rate,
            grain_flow_rate=grain_flow_rate,
            width=width,
            length=length,
            dryer_width=dryer_width,
            dryer_length=dryer_length,
            bed_depth=bed_depth,
            status='running'
        )
        db.session.add(simulation)
        db.session.flush()  # This populates the ID and default values like created_at
        db.session.commit()
        
        # Run simulation based on selected method
        try:
            results = simulate_drying(
                simulation.id,
                initial_moisture,
                target_moisture,
                grain_temp,
                air_temp,
                air_rh,
                air_flow_rate,
                model_type,
                processing_method
            )
            
            # Update simulation with results
            simulation.status = 'complete'
            simulation.total_time = results['total_time']
            simulation.total_energy = results['total_energy']
            simulation.total_water_removed = results['total_water_removed']
            simulation.final_moisture = results['final_moisture']
            simulation.completed_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'simulation_id': simulation.id,
                'results': results
            })
        
        except Exception as e:
            simulation.status = 'error'
            db.session.commit()
            import traceback
            error_details = {
                'error': str(e),
                'type': type(e).__name__,
                'traceback': traceback.format_exc()
            }
            print(f"Simulation error: {error_details}")  # Log to console
            return jsonify({'success': False, 'error': str(e), 'details': error_details}), 500
    
    except Exception as outer_error:
        # Catch errors that happen before simulation object is created
        import traceback
        error_details = {
            'error': str(outer_error),
            'type': type(outer_error).__name__,
            'traceback': traceback.format_exc()
        }
        print(f"Request processing error: {error_details}")
        return jsonify({'success': False, 'error': str(outer_error), 'details': error_details}), 500


def simulate_drying(simulation_id, initial_moisture, target_moisture, grain_temp, air_temp, air_rh, air_flow, model_type='exponential', processing_method='regular'):
    """
    Grain drying simulation with moisture gradient calculation
    
    Simulates drying through multiple layers of grain bed to show gradient
    """
    
    # Simulation parameters
    if processing_method == 'rk4':
        time_step = 0.05
        max_iterations = 1000
    else:
        time_step = 0.1
        max_iterations = 500
    
    # Bed layer setup - divide bed into layers for gradient
    num_layers = 5  # Bottom to top (air flows from bottom)
    layer_moisture = [initial_moisture] * num_layers  # Initialize all layers
    
    # Initialize variables
    total_time = 0.0
    total_energy = 0.0
    total_water_removed = 0.0
    iteration = 0
    
    # Drying rate constant (depends on model type)
    temp_factor = (air_temp - 60) / 50.0
    rh_factor = 1.0 - (air_rh / 100.0)
    
    # Model-specific constants
    if model_type == 'thompson':
        k = 0.18 * temp_factor * rh_factor
    elif model_type == 'page':
        k = 0.16 * temp_factor * rh_factor
        n = 1.2
    elif model_type == 'henderson_pabis':
        k = 0.15 * temp_factor * rh_factor
        a = 1.05
    else:
        k = 0.15 * temp_factor * rh_factor
    
    iterations_data = []
    previous_moisture = initial_moisture
    previous_time = 0.0
    
    while min(layer_moisture) > target_moisture and iteration < max_iterations:
        # Air properties change as it moves through layers
        current_air_temp = air_temp
        current_air_rh = air_rh
        
        # Process each layer from bottom (air inlet) to top
        for layer_idx in range(num_layers):
            equilibrium_moisture = 5.0 + (current_air_rh * 0.08)
            
            # Layer-specific drying - bottom layers dry faster
            layer_exposure = 1.0 - (layer_idx * 0.15)  # Bottom layer = 1.0, top = 0.4
            effective_k = k * layer_exposure
            
            # Calculate moisture change based on model
            current_moisture = layer_moisture[layer_idx]
            
            # Safety check - don't dry below equilibrium
            if current_moisture <= equilibrium_moisture:
                continue
            
            try:
                if model_type == 'page':
                    MR = (current_moisture - equilibrium_moisture) / (initial_moisture - equilibrium_moisture)
                    if MR > 0:
                        moisture_change = effective_k * (n * (MR ** (n-1))) * (current_moisture - equilibrium_moisture) * time_step
                    else:
                        moisture_change = 0
                elif model_type == 'henderson_pabis':
                    moisture_change = effective_k * a * (current_moisture - equilibrium_moisture) * time_step
                else:
                    moisture_change = effective_k * (current_moisture - equilibrium_moisture) * time_step
                
                # Apply processing method
                if processing_method == 'rk4':
                    k1 = effective_k * (current_moisture - equilibrium_moisture)
                    k2 = effective_k * ((current_moisture - k1*time_step/2) - equilibrium_moisture)
                    k3 = effective_k * ((current_moisture - k2*time_step/2) - equilibrium_moisture)
                    k4 = effective_k * ((current_moisture - k3*time_step) - equilibrium_moisture)
                    moisture_change = (k1 + 2*k2 + 2*k3 + k4) * time_step / 6
                
                # Ensure moisture doesn't go negative
                moisture_change = max(0, min(moisture_change, current_moisture - equilibrium_moisture))
                layer_moisture[layer_idx] -= moisture_change
                
                # Air picks up moisture and cools slightly as it moves up
                current_air_rh = min(100, current_air_rh + moisture_change * 0.5)
                current_air_temp = max(grain_temp, current_air_temp - (moisture_change * 0.2))
                
            except Exception as e:
                # If calculation fails, use simple exponential
                moisture_change = effective_k * (current_moisture - equilibrium_moisture) * time_step
                moisture_change = max(0, min(moisture_change, current_moisture - equilibrium_moisture))
                layer_moisture[layer_idx] -= moisture_change
        
        # Calculate average moisture and total water removed
        avg_moisture = sum(layer_moisture) / num_layers
        
        grain_mass_lb = 1000.0
        moisture_change_total = previous_moisture - avg_moisture
        water_removed_step = (moisture_change_total / 100.0) * grain_mass_lb
        total_water_removed += water_removed_step
        
        energy_step = water_removed_step * 1000.0
        total_energy += energy_step
        
        total_time += time_step
        iteration += 1
        
        # Calculate drying rate
        time_diff = total_time - previous_time
        drying_rate = (previous_moisture - avg_moisture) / time_diff if time_diff > 0 else 0
        
        # Store iteration data with gradient
        if iteration % 5 == 0 or min(layer_moisture) <= target_moisture:
            iter_data = IterationData(
                simulation_id=simulation_id,
                iteration=iteration,
                time=total_time,
                moisture=avg_moisture,
                drying_rate=drying_rate,
                energy=total_energy,
                water_removed=total_water_removed,
                grain_temp=grain_temp + (air_temp - grain_temp) * 0.3,
                air_temp=air_temp,
                moisture_gradient=json.dumps([round(m, 2) for m in layer_moisture])
            )
            db.session.add(iter_data)
            iterations_data.append(iter_data.to_dict())
            
            previous_moisture = avg_moisture
            previous_time = total_time
    
    db.session.commit()
    
    return {
        'total_time': round(total_time, 2),
        'total_energy': round(total_energy, 0),
        'total_water_removed': round(total_water_removed, 2),
        'final_moisture': round(avg_moisture, 2),
        'iterations': iteration,
        'model_used': model_type,
        'method_used': processing_method,
        'iterations_data': iterations_data
    }


@app.route('/api/simulation/<int:sim_id>', methods=['GET'])
def get_simulation(sim_id):
    """Get simulation details and all iteration data"""
    simulation = Simulation.query.get_or_404(sim_id)
    iterations = IterationData.query.filter_by(simulation_id=sim_id).order_by(IterationData.iteration).all()
    
    return jsonify({
        'simulation': simulation.to_dict(),
        'iterations': [iter.to_dict() for iter in iterations]
    })


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get all past simulations"""
    simulations = Simulation.query.order_by(Simulation.created_at.desc()).limit(50).all()
    return jsonify([sim.to_dict() for sim in simulations])


@app.route('/api/simulation/<int:sim_id>/stop', methods=['POST'])
def stop_simulation(sim_id):
    """Stop a running simulation"""
    simulation = Simulation.query.get_or_404(sim_id)
    simulation.status = 'stopped'
    simulation.completed_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True, 'message': 'Simulation stopped'})


@app.route('/api/comments', methods=['POST'])
def add_comment():
    """Add a comment/review to a simulation"""
    data = request.json
    
    comment = Comment(
        simulation_id=data.get('simulation_id'),
        author=data.get('author', 'Anonymous'),
        rating=int(data.get('rating', 3)),
        comment=data.get('comment', '')
    )
    
    db.session.add(comment)
    db.session.commit()
    
    return jsonify({'success': True, 'comment': comment.to_dict()})


@app.route('/api/simulation/<int:sim_id>/comments', methods=['GET'])
def get_simulation_comments(sim_id):
    """Get all comments for a simulation"""
    comments = Comment.query.filter_by(simulation_id=sim_id).order_by(Comment.created_at.desc()).all()
    return jsonify([comment.to_dict() for comment in comments])


@app.route('/api/dashboard_settings/<page_name>', methods=['GET'])
def get_dashboard_settings(page_name):
    """Get dashboard settings for a specific page"""
    settings = DashboardSettings.query.filter_by(page_name=page_name).first()
    if settings:
        return jsonify(settings.to_dict())
    else:
        # Return defaults
        return jsonify({
            'page_name': page_name,
            'title': '',
            'subtitle': '',
            'description': ''
        })


@app.route('/api/dashboard_settings', methods=['POST'])
def save_dashboard_settings():
    """Save or update dashboard settings for a page"""
    data = request.json
    page_name = data.get('page_name')
    
    # Check if settings exist
    settings = DashboardSettings.query.filter_by(page_name=page_name).first()
    
    if settings:
        # Update existing
        settings.title = data.get('title')
        settings.subtitle = data.get('subtitle')
        settings.description = data.get('description')
        settings.title_font = data.get('title_font')
        settings.title_size = data.get('title_size')
        settings.title_color = data.get('title_color')
        settings.title_bg_color = data.get('title_bg_color')
        settings.subtitle_font = data.get('subtitle_font')
        settings.subtitle_size = data.get('subtitle_size')
        settings.subtitle_color = data.get('subtitle_color')
        settings.description_font = data.get('description_font')
        settings.description_size = data.get('description_size')
        settings.description_color = data.get('description_color')
        settings.page_bg_color = data.get('page_bg_color')
        settings.content_bg_color = data.get('content_bg_color')
    else:
        # Create new
        settings = DashboardSettings(
            page_name=page_name,
            title=data.get('title'),
            subtitle=data.get('subtitle'),
            description=data.get('description'),
            title_font=data.get('title_font'),
            title_size=data.get('title_size'),
            title_color=data.get('title_color'),
            title_bg_color=data.get('title_bg_color'),
            subtitle_font=data.get('subtitle_font'),
            subtitle_size=data.get('subtitle_size'),
            subtitle_color=data.get('subtitle_color'),
            description_font=data.get('description_font'),
            description_size=data.get('description_size'),
            description_color=data.get('description_color'),
            page_bg_color=data.get('page_bg_color'),
            content_bg_color=data.get('content_bg_color')
        )
        db.session.add(settings)
    
    db.session.commit()
    
    return jsonify({'success': True, 'settings': settings.to_dict()})


@app.route('/crop_master')
def crop_master():
    """Crop management page"""
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    crops = Crop.query.all()
    response = make_response(render_template('crop_master.html', crops=crops))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response


@app.route('/history')
def history():
    """Simulation history page"""
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    # Show only current user's simulations
    user_id = session.get('user_id')
    simulations = Simulation.query.filter_by(user_id=user_id).order_by(Simulation.created_at.desc()).limit(50).all()
    response = make_response(render_template('history.html', simulations=simulations))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response


@app.route('/reports')
def reports():
    """Reports page"""
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    # Show only current user's completed simulations
    user_id = session.get('user_id')
    simulations = Simulation.query.filter_by(user_id=user_id, status='complete').order_by(Simulation.created_at.desc()).limit(20).all()
    response = make_response(render_template('reports.html', simulations=simulations))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response


@app.route('/settings')
def settings():
    """Settings/Appearance customization page"""
    # Check if user is admin (simple check for now)
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user and not user.is_admin:
            return "Access Denied: Admin only", 403
    return render_template('settings.html')


@app.route('/login')
def login_page():
    """Login/Register page"""
    return render_template('login.html')


@app.route('/register')
def register_page():
    """Redirect to login page (unified login/register)"""
    return redirect(url_for('login_page'))


@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('index'))


@app.route('/api/login', methods=['POST'])
def api_login():
    """Handle login API request"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    remember = data.get('remember', False)
    
    # Find user by username or email
    user = User.query.filter(
        (User.username == username) | (User.email == username)
    ).first()
    
    if not user:
        return jsonify({'success': False, 'user_not_found': True})
    
    if user.check_password(password):
        # Set session
        session['user_id'] = user.id
        session['username'] = user.username
        session['is_admin'] = user.is_admin
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'redirect': '/',
            'user': user.to_dict()
        })
    else:
        return jsonify({'success': False, 'error': 'Invalid password'})


@app.route('/api/register', methods=['POST'])
def api_register():
    """Handle registration API request"""
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    
    # Check if username exists
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'error': 'Username already exists'})
    
    # Check if email exists
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'error': 'Email already exists'})
    
    # Create new user
    user = User(
        username=username,
        email=email,
        full_name=full_name,
        is_admin=False  # First user will be made admin by init_db
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    # Auto-login after registration
    session['user_id'] = user.id
    session['username'] = user.username
    session['is_admin'] = user.is_admin
    
    return jsonify({
        'success': True,
        'redirect': '/',
        'user': user.to_dict()
    })


@app.route('/api/current_user', methods=['GET'])
def get_current_user():
    """Get current logged-in user info"""
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify({
                'logged_in': True,
                'user': user.to_dict()
            })
    return jsonify({'logged_in': False})


@app.route('/api/forgot_password', methods=['POST'])
def forgot_password():
    """Send password reset code to user's email"""
    data = request.json
    email = data.get('email')
    
    # Find user by email
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({'success': False, 'error': 'Email not found'})
    
    # Generate 6-digit reset code
    reset_code = ''.join(random.choices(string.digits, k=6))
    
    # Create password reset record
    password_reset = PasswordReset(
        user_id=user.id,
        email=email,
        reset_code=reset_code,
        expires_at=datetime.utcnow() + timedelta(hours=1)  # Valid for 1 hour
    )
    
    db.session.add(password_reset)
    db.session.commit()
    
    # TODO: Send email with reset code
    # For now, just print to console
    print(f"\n{'='*50}")
    print(f"PASSWORD RESET CODE FOR {email}")
    print(f"Code: {reset_code}")
    print(f"Valid for 1 hour")
    print(f"{'='*50}\n")
    
    # In production, use email service:
    # send_email(email, "Password Reset Code", f"Your reset code is: {reset_code}")
    
    return jsonify({
        'success': True,
        'message': 'Reset code sent to email',
        'code': reset_code  # Remove this in production!
    })


@app.route('/api/reset_password', methods=['POST'])
def reset_password():
    """Reset password using code"""
    data = request.json
    email = data.get('email')
    code = data.get('code')
    new_password = data.get('password')
    
    # Find the most recent valid reset code for this email
    password_reset = PasswordReset.query.filter_by(
        email=email,
        reset_code=code,
        is_used=False
    ).order_by(PasswordReset.created_at.desc()).first()
    
    if not password_reset:
        return jsonify({'success': False, 'error': 'Invalid or expired code'})
    
    # Check if code is still valid (not expired)
    if not password_reset.is_valid():
        return jsonify({'success': False, 'error': 'Code has expired'})
    
    # Get user and update password
    user = User.query.get(password_reset.user_id)
    if not user:
        return jsonify({'success': False, 'error': 'User not found'})
    
    # Set new password
    user.set_password(new_password)
    
    # Mark reset code as used
    password_reset.is_used = True
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Password reset successfully'
    })


@app.route('/results/<int:sim_id>')
def show_results(sim_id):
    """Display detailed results page for a simulation"""
    simulation = Simulation.query.get_or_404(sim_id)
    iterations = IterationData.query.filter_by(simulation_id=sim_id).order_by(IterationData.iteration).all()
    
    # Prepare data for template
    user_info = {
        'user_name': 'User',  # You can add these fields to Simulation model if needed
        'project_name': 'Grain Drying Project',
        'address': 'Local'
    }
    
    summary = {
        'final_moisture_pct': simulation.final_moisture or 0,
        'total_time_hr': simulation.total_time or 0,
        'moisture_removed_pct': (simulation.initial_moisture - simulation.final_moisture) if simulation.final_moisture else 0
    }
    
    input_params = {
        'initial_moisture': simulation.initial_moisture,
        'grain_temp': simulation.grain_temp,
        'air_temp': simulation.air_temp,
        'rel_humidity': simulation.air_rh,
        'air_flow_cfm': simulation.air_flow_rate,
        'bed_depth': simulation.length  # Using length as bed depth for now
    }
    
    # Prepare time series data with gradients
    time_series = []
    times = []
    moistures = []
    drying_rates = []
    gradients = []  # Store all gradient data
    
    for iter_data in iterations:
        time_series.append({
            'time_hr': iter_data.time,
            'avg_moisture_pct': iter_data.moisture,
            'drying_rate': iter_data.drying_rate or 0,
            'energy_btu': iter_data.energy,
            'water_removed_lb': iter_data.water_removed
        })
        times.append(iter_data.time)
        moistures.append(iter_data.moisture)
        drying_rates.append(iter_data.drying_rate or 0)
        
        # Extract gradient data
        gradient = json.loads(iter_data.moisture_gradient) if iter_data.moisture_gradient else None
        gradients.append(gradient)
    
    return render_template('results.html',
                         user_info=user_info,
                         summary=summary,
                         crop_name=simulation.crop.name if simulation.crop else 'Unknown',
                         model_type=simulation.model_type or 'exponential',
                         processing_method=simulation.processing_method or 'regular',
                         input_params=input_params,
                         time_series=time_series,
                         times=times,
                         moistures=moistures,
                         drying_rates=drying_rates,
                         gradients=gradients,
                         sim_id=sim_id)


@app.route('/download_pdf/<int:sim_id>')
def download_pdf(sim_id):
    """Download PDF report (placeholder)"""
    return jsonify({
        'message': 'PDF generation coming soon!',
        'sim_id': sim_id
    })


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
