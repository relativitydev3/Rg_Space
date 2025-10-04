class DemoController {
    constructor() {
        this.demoContent = document.getElementById('demoContent');
        this.init();
    }

    init() {
        this.loadDemoInterface();
    }

    loadDemoInterface() {
        // Load the interactive demo interface
        this.demoContent.innerHTML = `
            <div class="demo-interface">
                <div class="demo-header p-4 border-bottom">
                    <h4 class="text-light mb-0">
                        <i class="fas fa-search me-2"></i>Analizador de Curvas de Luz
                    </h4>
                </div>
                
                <div class="demo-body p-4">
                    <div class="row">
                        <div class="col-md-8">
                            <div class="chart-container mb-4">
                                <canvas id="demoLightCurve" height="250"></canvas>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="controls-container">
                                <h6 class="text-warning mb-3">Parámetros del Tránsito</h6>
                                
                                <div class="mb-3">
                                    <label class="form-label text-light small">Período Orbital</label>
                                    <input type="range" class="form-range" id="demoPeriod" min="1" max="50" value="15">
                                    <div class="d-flex justify-content-between">
                                        <small class="text-muted">1 día</small>
                                        <span id="demoPeriodValue" class="text-warning">15 días</span>
                                        <small class="text-muted">50 días</small>
                                    </div>
                                </div>

                                <div class="mb-3">
                                    <label class="form-label text-light small">Profundidad</label>
                                    <input type="range" class="form-range" id="demoDepth" min="100" max="10000" value="650">
                                    <div class="d-flex justify-content-between">
                                        <small class="text-muted">100 ppm</small>
                                        <span id="demoDepthValue" class="text-warning">650 ppm</span>
                                        <small class="text-muted">10000 ppm</small>
                                    </div>
                                </div>

                                <button class="btn btn-warning w-100 mt-3" id="analyzeDemo">
                                    <i class="fas fa-brain me-2"></i>Analizar con IA
                                </button>
                            </div>
                        </div>
                    </div>
                    
                    <div class="results-container mt-4">
                        <div id="demoResults" class="text-center">
                            <p class="text-muted">Ajusta los parámetros y haz clic en "Analizar con IA"</p>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.initializeDemoChart();
        this.setupDemoControls();
    }

    initializeDemoChart() {
        const ctx = document.getElementById('demoLightCurve').getContext('2d');
        
        // Generate sample light curve data
        const data = this.generateLightCurveData(15, 650);
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Curva de Luz',
                    data: data.values,
                    borderColor: '#00b4d8',
                    backgroundColor: 'rgba(0, 180, 216, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Tiempo (días)',
                            color: '#9CA3AF'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#9CA3AF'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Flujo Normalizado',
                            color: '#9CA3AF'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#9CA3AF'
                        },
                        min: 0.98,
                        max: 1.005
                    }
                }
            }
        });
    }

    setupDemoControls() {
        // Period slider
        const periodSlider = document.getElementById('demoPeriod');
        const periodValue = document.getElementById('demoPeriodValue');
        
        periodSlider.addEventListener('input', (e) => {
            const value = e.target.value;
            periodValue.textContent = `${value} días`;
            this.updateDemoChart();
        });

        // Depth slider
        const depthSlider = document.getElementById('demoDepth');
        const depthValue = document.getElementById('demoDepthValue');
        
        depthSlider.addEventListener('input', (e) => {
            const value = e.target.value;
            depthValue.textContent = `${value} ppm`;
            this.updateDemoChart();
        });

        // Analyze button
        document.getElementById('analyzeDemo').addEventListener('click', () => {
            this.analyzeTransit();
        });
    }

    generateLightCurveData(period, depthPPM) {
        const labels = [];
        const values = [];
        const points = 300;
        const depth = depthPPM / 1000000;

        for (let i = 0; i < points; i++) {
            const x = (i / points) * (period * 3); // Show 3 periods
            labels.push(x.toFixed(1));
            
            let y = 1 + (Math.random() - 0.5) * 0.002; // Base noise
            
            // Add transits
            const phase = (x % period) / period;
            if (phase > 0.48 && phase < 0.52) {
                y = 1 - depth + (Math.random() - 0.5) * 0.001;
            }
            
            values.push(y);
        }

        return { labels, values };
    }

    updateDemoChart() {
        // This would update the chart in a real implementation
        console.log('Updating demo chart...');
    }

    analyzeTransit() {
        const period = document.getElementById('demoPeriod').value;
        const depth = document.getElementById('demoDepth').value;
        
        // Simulate AI analysis
        const confidence = Math.min(95, 30 + (depth / 100) + (Math.random() * 20));
        const isExoplanet = confidence > 60;

        const resultsHTML = `
            <div class="alert ${isExoplanet ? 'alert-success' : 'alert-warning'}">
                <h5>
                    <i class="fas fa-${isExoplanet ? 'check-circle' : 'exclamation-triangle'} me-2"></i>
                    ${isExoplanet ? '¡Posible Exoplaneta Detectado!' : 'Señal No Concluyente'}
                </h5>
                <p class="mb-2">Confianza del análisis: <strong>${Math.round(confidence)}%</strong></p>
                <small class="text-muted">
                    ${isExoplanet ? 
                        'La señal muestra características consistentes con un tránsito planetario.' :
                        'Se requieren más datos para confirmar la naturaleza de la señal.'
                    }
                </small>
            </div>
        `;

        document.getElementById('demoResults').innerHTML = resultsHTML;
    }
}