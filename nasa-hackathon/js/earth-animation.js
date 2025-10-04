class EarthAnimation {
    constructor() {
        this.earth = document.getElementById('earth');
        this.rotation = 0;
        this.init();
    }

    init() {
        this.setupScrollRotation();
        this.addCloudDetails();
    }

    setupScrollRotation() {
        let lastScrollY = window.scrollY;
        let rotation = 0;

        const updateRotation = () => {
            const scrollY = window.scrollY;
            const scrollDelta = scrollY - lastScrollY;
            
            // Adjust rotation speed based on scroll delta
            rotation += scrollDelta * 0.2;
            
            // Apply rotation with smooth easing
            this.earth.style.transform = `rotate(${rotation}deg)`;
            
            lastScrollY = scrollY;
            requestAnimationFrame(updateRotation);
        };

        requestAnimationFrame(updateRotation);
    }

    addCloudDetails() {
        // Add additional cloud layers for more realism
        const cloudLayer = document.createElement('div');
        cloudLayer.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            border-radius: 50%;
            background: 
                radial-gradient(circle at 40% 40%, rgba(255,255,255,0.2) 0%, transparent 50%),
                radial-gradient(circle at 60% 70%, rgba(255,255,255,0.15) 0%, transparent 50%),
                radial-gradient(circle at 30% 80%, rgba(255,255,255,0.1) 0%, transparent 50%);
            animation: cloudMove 15s linear infinite reverse;
            opacity: 0.6;
        `;
        
        this.earth.appendChild(cloudLayer);
    }
}