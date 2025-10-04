// Main Application Controller
class ExoDetectApp {
    constructor() {
        this.components = {};
        this.init();
    }

    init() {
        // Initialize all components
        this.components.header = new HeaderController();
        this.components.earth = new EarthAnimation();
        this.components.scroll = new ScrollAnimations();
        this.components.hero = new HeroSection();
        this.components.demo = new DemoController();

        // Initialize method chart
        this.initMethodChart();

        console.log('🚀 ExoDetect App Initialized');
    }

    initMethodChart() {
        const ctx = document.getElementById('methodChart').getContext('2d');
        
        // Sample light curve data for method demonstration
        const labels = [];
        const lightCurve = [];
        const points = 200;

        for (let i = 0; i < points; i++) {
            const x = (i / points) * 10;
            labels.push(x.toFixed(1));
            
            let y = 1 + (Math.random() - 0.5) * 0.01; // Base noise
            
            // Add transit at specific positions
            if ((x > 2.5 && x < 2.7) || (x > 7.5 && x < 7.7)) {
                y = 0.985 + (Math.random() - 0.5) * 0.005; // Transit depth
            }
            
            lightCurve.push(y);
        }

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Curva de Luz',
                    data: lightCurve,
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
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
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
                            text: 'Brillo Normalizado',
                            color: '#9CA3AF'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#9CA3AF'
                        },
                        min: 0.975,
                        max: 1.015
                    }
                }
            }
        });
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new ExoDetectApp();
});