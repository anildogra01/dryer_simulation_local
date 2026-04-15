/**
 * Dryer Simulation Frontend Integration
 * ======================================
 * 
 * JavaScript code to integrate dryer simulation API with your web frontend.
 * Works with the Flask API backend.
 * 
 * Usage: Include this in your Crop Master Management web app
 */

class DryerSimulationClient {
    constructor(apiBaseUrl = 'http://localhost:5000/api') {
        this.apiBaseUrl = apiBaseUrl;
    }

    /**
     * Make API request
     */
    async makeRequest(endpoint, method = 'GET', data = null) {
        const url = `${this.apiBaseUrl}${endpoint}`;
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            }
        };

        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url, options);
            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'API request failed');
            }

            return result;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    /**
     * Get crop property presets
     */
    async getCropPresets() {
        return await this.makeRequest('/crops/presets', 'GET');
    }

    /**
     * Run crossflow dryer simulation
     */
    async runCrossflowSimulation(inputs) {
        return await this.makeRequest('/dryer/crossflow', 'POST', inputs);
    }

    /**
     * Calculate psychrometric properties
     */
    async calculatePsychrometric(tempF, rh) {
        return await this.makeRequest('/dryer/psychrometric', 'POST', {
            temp_f: tempF,
            rh: rh
        });
    }

    /**
     * Validate parameters
     */
    async validateParameters(inputs) {
        return await this.makeRequest('/dryer/validate', 'POST', inputs);
    }

    /**
     * Estimate drying time
     */
    async estimateDryingTime(params) {
        return await this.makeRequest('/dryer/estimate-time', 'POST', params);
    }
}


/**
 * UI Helper Functions
 */
class DryerSimulationUI {
    constructor(apiClient) {
        this.api = apiClient;
    }

    /**
     * Populate crop selection dropdown
     */
    async populateCropDropdown(selectElementId) {
        try {
            const result = await this.api.getCropPresets();
            const selectElement = document.getElementById(selectElementId);
            
            if (!selectElement) {
                console.error(`Element ${selectElementId} not found`);
                return;
            }

            // Clear existing options
            selectElement.innerHTML = '<option value="">Select crop...</option>';

            // Add crop options
            for (const [cropName, cropData] of Object.entries(result.crops)) {
                const option = document.createElement('option');
                option.value = cropName;
                option.textContent = cropData.name;
                option.dataset.cropData = JSON.stringify(cropData);
                selectElement.appendChild(option);
            }

            return result.crops;
        } catch (error) {
            console.error('Error populating crops:', error);
            this.showError('Failed to load crop presets');
        }
    }

    /**
     * Run simulation from form data
     */
    async runSimulationFromForm(formId) {
        try {
            const form = document.getElementById(formId);
            if (!form) {
                throw new Error(`Form ${formId} not found`);
            }

            // Show loading indicator
            this.showLoading('Running simulation...');

            // Get form data
            const formData = new FormData(form);
            
            // Get selected crop data
            const cropSelect = form.querySelector('[name="crop"]');
            const selectedOption = cropSelect.options[cropSelect.selectedIndex];
            const cropData = JSON.parse(selectedOption.dataset.cropData);

            // Build inputs object
            const inputs = {
                crop: cropData,
                initial_grain_temp: parseFloat(formData.get('initial_grain_temp')),
                inlet_air_temp: parseFloat(formData.get('inlet_air_temp')),
                inlet_air_rh: parseFloat(formData.get('inlet_air_rh')),
                target_moisture: parseFloat(formData.get('target_moisture')),
                airflow_cfm: parseFloat(formData.get('airflow_cfm')),
                grain_flow_bph: parseFloat(formData.get('grain_flow_bph')),
                width: parseFloat(formData.get('width')),
                length: parseFloat(formData.get('length'))
            };

            // Validate first
            const validation = await this.api.validateParameters(inputs);
            if (!validation.valid) {
                this.hideLoading();
                this.showValidationErrors(validation.errors, validation.warnings);
                return null;
            }

            // Run simulation
            const result = await this.api.runCrossflowSimulation(inputs);
            
            this.hideLoading();
            
            if (result.success) {
                this.displayResults(result.outputs);
                return result;
            } else {
                throw new Error(result.error);
            }

        } catch (error) {
            this.hideLoading();
            this.showError(`Simulation failed: ${error.message}`);
            return null;
        }
    }

    /**
     * Display simulation results
     */
    displayResults(outputs) {
        const resultsDiv = document.getElementById('simulationResults');
        if (!resultsDiv) {
            console.error('Results div not found');
            return;
        }

        const html = `
            <div class="results-container">
                <h3>Simulation Results</h3>
                
                <div class="result-section">
                    <h4>Drying Performance</h4>
                    <div class="result-row">
                        <span class="label">Final Moisture:</span>
                        <span class="value">${outputs.final_moisture.toFixed(2)}% db</span>
                    </div>
                    <div class="result-row">
                        <span class="label">Moisture Removed:</span>
                        <span class="value">${outputs.moisture_removed.toFixed(2)} points</span>
                    </div>
                    <div class="result-row">
                        <span class="label">Drying Time:</span>
                        <span class="value">${outputs.drying_time.toFixed(2)} hours</span>
                    </div>
                    <div class="result-row">
                        <span class="label">Target Achieved:</span>
                        <span class="value ${outputs.target_achieved ? 'success' : 'warning'}">
                            ${outputs.target_achieved ? '✓ Yes' : '✗ No'}
                        </span>
                    </div>
                </div>

                <div class="result-section">
                    <h4>Energy & Efficiency</h4>
                    <div class="result-row">
                        <span class="label">Energy Consumed:</span>
                        <span class="value">${outputs.energy_consumed.toFixed(0)} BTU</span>
                    </div>
                    <div class="result-row">
                        <span class="label">Air/Grain Ratio:</span>
                        <span class="value">${outputs.air_grain_ratio.toFixed(3)}</span>
                    </div>
                    <div class="result-row">
                        <span class="label">Heat Transfer Coef:</span>
                        <span class="value">${outputs.heat_transfer_coeff.toFixed(2)} BTU/hr-ft²-°F</span>
                    </div>
                    <div class="result-row">
                        <span class="label">Equilibrium MC:</span>
                        <span class="value">${outputs.equilibrium_moisture.toFixed(2)}% db</span>
                    </div>
                </div>

                <div class="result-section">
                    <h4>Mass Flows</h4>
                    <div class="result-row">
                        <span class="label">Air Mass Flow:</span>
                        <span class="value">${outputs.air_mass_flow.toFixed(2)} lb/hr</span>
                    </div>
                    <div class="result-row">
                        <span class="label">Grain Mass Flow:</span>
                        <span class="value">${outputs.grain_mass_flow.toFixed(2)} lb/hr</span>
                    </div>
                    <div class="result-row">
                        <span class="label">Water Removed:</span>
                        <span class="value">${outputs.water_removed.toFixed(2)} lb/hr</span>
                    </div>
                </div>

                ${outputs.warnings && outputs.warnings.length > 0 ? `
                <div class="result-section warnings">
                    <h4>⚠ Warnings</h4>
                    ${outputs.warnings.map(w => `<div class="warning-item">${w}</div>`).join('')}
                </div>
                ` : ''}
            </div>
        `;

        resultsDiv.innerHTML = html;
        resultsDiv.style.display = 'block';
    }

    /**
     * Show validation errors
     */
    showValidationErrors(errors, warnings) {
        let message = '';
        
        if (errors.length > 0) {
            message += '<strong>Errors:</strong><ul>';
            errors.forEach(err => {
                message += `<li>${err}</li>`;
            });
            message += '</ul>';
        }

        if (warnings.length > 0) {
            message += '<strong>Warnings:</strong><ul>';
            warnings.forEach(warn => {
                message += `<li>${warn}</li>`;
            });
            message += '</ul>';
        }

        this.showError(message);
    }

    /**
     * Show loading indicator
     */
    showLoading(message = 'Loading...') {
        const loadingDiv = document.getElementById('loadingIndicator') || this.createLoadingDiv();
        loadingDiv.textContent = message;
        loadingDiv.style.display = 'block';
    }

    /**
     * Hide loading indicator
     */
    hideLoading() {
        const loadingDiv = document.getElementById('loadingIndicator');
        if (loadingDiv) {
            loadingDiv.style.display = 'none';
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        alert(message); // Replace with your preferred error display method
    }

    /**
     * Create loading div if it doesn't exist
     */
    createLoadingDiv() {
        const div = document.createElement('div');
        div.id = 'loadingIndicator';
        div.style.cssText = 'position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.2); z-index: 9999;';
        document.body.appendChild(div);
        return div;
    }
}


/**
 * Example Usage
 * =============
 */

// Initialize when page loads
document.addEventListener('DOMContentLoaded', async function() {
    
    // Create API client
    const apiClient = new DryerSimulationClient('http://localhost:5000/api');
    const ui = new DryerSimulationUI(apiClient);

    // Populate crop dropdown
    await ui.populateCropDropdown('cropSelect');

    // Handle form submission
    const simulationForm = document.getElementById('dryerSimulationForm');
    if (simulationForm) {
        simulationForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            await ui.runSimulationFromForm('dryerSimulationForm');
        });
    }

    // Quick estimate button
    const estimateButton = document.getElementById('estimateTimeButton');
    if (estimateButton) {
        estimateButton.addEventListener('click', async function() {
            const initialMC = parseFloat(document.getElementById('initial_moisture').value);
            const targetMC = parseFloat(document.getElementById('target_moisture').value);
            const airTemp = parseFloat(document.getElementById('inlet_air_temp').value);
            const airRH = parseFloat(document.getElementById('inlet_air_rh').value);

            try {
                const result = await apiClient.estimateDryingTime({
                    initial_moisture: initialMC,
                    target_moisture: targetMC,
                    inlet_air_temp: airTemp,
                    inlet_air_rh: airRH
                });

                if (result.success) {
                    alert(`Estimated drying time: ${result.estimated_drying_time_hours} hours\n${result.note}`);
                }
            } catch (error) {
                ui.showError('Failed to estimate drying time');
            }
        });
    }
});


/**
 * Example HTML Form
 * =================
 * 
 * Add this to your Crop Master Management page:
 * 
 * <form id="dryerSimulationForm">
 *     <h3>Dryer Simulation</h3>
 *     
 *     <label>Select Crop:</label>
 *     <select name="crop" id="cropSelect" required>
 *         <option value="">Loading...</option>
 *     </select>
 *     
 *     <label>Initial Grain Temperature (°F):</label>
 *     <input type="number" name="initial_grain_temp" value="60" step="0.1" required>
 *     
 *     <label>Inlet Air Temperature (°F):</label>
 *     <input type="number" name="inlet_air_temp" id="inlet_air_temp" value="180" step="0.1" required>
 *     
 *     <label>Inlet Air RH (%):</label>
 *     <input type="number" name="inlet_air_rh" id="inlet_air_rh" value="5" step="0.1" required>
 *     
 *     <label>Target Moisture (% db):</label>
 *     <input type="number" name="target_moisture" id="target_moisture" value="15" step="0.1" required>
 *     
 *     <label>Airflow (CFM):</label>
 *     <input type="number" name="airflow_cfm" value="1000" step="1" required>
 *     
 *     <label>Grain Flow (bu/hr):</label>
 *     <input type="number" name="grain_flow_bph" value="100" step="1" required>
 *     
 *     <label>Dryer Width (ft):</label>
 *     <input type="number" name="width" value="2.0" step="0.1" required>
 *     
 *     <label>Dryer Length (ft):</label>
 *     <input type="number" name="length" value="10.0" step="0.1" required>
 *     
 *     <button type="button" id="estimateTimeButton">Quick Time Estimate</button>
 *     <button type="submit">Run Simulation</button>
 * </form>
 * 
 * <div id="simulationResults" style="display: none;"></div>
 * <div id="loadingIndicator" style="display: none;">Running simulation...</div>
 */
